import logging
from hippo import pdf_creator
import json
import os
import queue
import requests
import shutil
from io import StringIO, BytesIO
import tempfile
import threading
import traceback
from hippo import util as c

from hippo.schemas.validate_schemas import SchemaValidationException, validate_project_config
from hippo.screenshot_thread import DEFAULT_SCREENSHOT_THREAD_COUNT, ScreenshotThread
from src.the_ark.email_client import EmailClientException
from src.the_ark.rhino_client import RhinoClientException
from src.the_ark.s3_client import S3Client, S3ClientException
from src.the_ark.screen_capture import DEFAULT_SCROLL_PADDING
from src.the_ark import selenium_helpers

log = c.create_logger("Request Thread")
request_queue = queue.Queue()


class Request(threading.Thread):
    def __init__(self, config=c.DEFAULT_APP_CONFIG):
        threading.Thread.__init__(self)
        self.is_alive = True
        self.environment = config[c.HIPPO_ENVIRONMENT]
        self.s3_bucket = config[c.HIPPO_S3_BUCKET]
        self.s3 = S3Client(self.s3_bucket)
        self.mandrill_key = config.get(c.MANDRILL_KEY, None)
        self.rhino_host = config[c.RHINO_HOST]
        self.content_path = ""
        self.allow_base_capture = config[c.ALLOW_BASE_CAPTURE]

        # Git Settings
        self.repo = config[c.GITHUB_REPO]
        self.github_token = config.get(c.GITHUB_TOKEN)
        self.github_directory = config.get(c.GITHUB_DIRECTORY, '')
        self.github_branch = config[c.GITHUB_BRANCH]
        if not self.github_branch:
            # Default the git branch to develop if not set and not running on production
            self.github_branch = "develop" if self.environment not in ["production"] else "production"

        # AEM tish
        self.username = config.get(c.HIPPO_AEM_USERNAME)
        self.password = config.get(c.HIPPO_AEM_PASSWORD)

        self.pfizer_username = config.get(c.PFIZER_USERNAME)
        self.pfizer_password = config.get(c.PFIZER_PASSWORD)
        self.pfizer_url = config.get(c.PFIZER_AUTH_URL)

        self.sauce_labs_username = config.get(c.SAUCE_LABS_USERNAME)
        self.sauce_labs_access_key = config.get(c.SAUCE_LABS_ACCESS_KEY)

    def run(self):
        while self.is_alive:
            request_data = request_queue.get()
            try:
                self.process_request(request_data)
            except KeyboardInterrupt:
                self.is_alive = False
            except c.HippoGeneralException as hippo_error:
                log.error(hippo_error)
            except Exception as e:
                log.error(f"Unexpected exception occurred when attempting to process request: {request_data}. Exception: {e}")
            finally:
                request_queue.task_done()

    def process_request(self, request_data):
        screenshot_thread_list = []
        error_list = []
        project_config = {}
        screenshot_queue = queue.Queue()

        # - Parse the data from the request
        requested_project, branch, send_to_rhino, url, browser, browser_size, user, build_id, site_paths, site_sections, \
        skip_sections, mobile, file_extension, local_path, recipients, custom_inputs, \
        requested_pagination = self.parse_request_data(request_data)

        sanitized_url = c.remove_basic_auth(url)

        image_list = {
            "user": user,
            "build_ID": build_id,
            "project": requested_project,
            "branch": branch,
            "mobile": mobile,
            "driver_data": browser,
            "image_list": [],
            "test_url": sanitized_url
        }


        pdf_image_list = {}

        # - Set up the path in which the screenshots will be stored
        s3_image_path = f"hippo/screenshots/{requested_project}/{branch}/{build_id}"
        local_image_path = tempfile.mkdtemp() + "/"

        # Fetch down the requested project's configuration file
        try:
            project_config = self.get_configuration(requested_project, branch, local_path)
            log.info(f"Retrieved project config file {project_config}")
        except SchemaValidationException as e:
            message = f"Project config failed Schema Validation... will continue with a base capture | {e}"
            log.warn(message)
        except ValueError as value_error:
            message = f"An error was found with the Json file when attempting to open the configuration " \
                      f"for '{requested_project}' | Error: {value_error}"
            log.error(message)
            error_list.append(message)
            self._output_screenshot_log(requested_project, sanitized_url, branch, send_to_rhino, build_id, user,
                                        image_list, error_list, s3_image_path, recipients, request_data["start_date"],
                                        request_data["start_time"], site_sections, skip_sections)
            raise value_error
        except (S3ClientException, Exception) as e:
            if not self.allow_base_capture:
                message = f"Unable to pull down and open the configuration for '{requested_project}' | " \
                          "Error: {e}"
                log.error(message)
                request_queue.task_done()
                error_list.append(message)
                self._output_screenshot_log(requested_project, sanitized_url, branch, send_to_rhino, build_id, user,
                                            image_list, error_list, s3_image_path, recipients,
                                            request_data["start_date"], request_data["start_time"], site_sections,
                                            skip_sections)
                raise e

        # - Warn the user if a configuration for the project does not exist
        if not project_config:
            message = f"A configuration doesn't exist for project '{requested_project}'. " \
                      "Going to run a base capture..."
            log.warn(message)
            error_list.append(message)
            project_config = {"ConfigExists": False}

        project = project_config.get(c.PROJECT, requested_project)
        thread_count = request_data.get(c.THREAD_COUNT) or project_config.get(c.THREAD_COUNT) or DEFAULT_SCREENSHOT_THREAD_COUNT

        action_libraries = self.get_action_libraries()


        # Create content path if running on a platform site
        self.content_path = request_data.get(c.CONTENT_PATH, "")
        if not self.content_path and project_config.get(c.PLATFORM):
            self.content_path = project_config.get(c.CONTENT_PATH, f"/content/{project}/en_us")

        try:
            try:
                # - Gather the urls for the site, and the break out the sections that should be skipped, etc.
                # If the "use_sauce_labs" option is set to True verify that there is a tunnel up and running for Hippo to use.
                running_tunnel = False
                if browser.get(c.USE_SAUCE_LABS):
                    running_tunnel = c.get_active_sauce_tunnel(self.sauce_labs_username, self.sauce_labs_access_key)

                if running_tunnel:
                    # If the project is Access Solutions it will set the max duration to 3 hours.
                    if "accesssolutions" in request_data.get(c.PROJECT):
                        browser.update({"maxDuration": 10800})

                    # If Firefox is being used on Sauce Labs the version used will be 62 so the job goes smoothly.
                    if "firefox" == request_data.get(c.BROWSER).get("browserName"):
                        browser.update({"version": 62})

                    # Updating the browser object to contain all the necessary items to run on Sauce Labs.
                    browser.update({"username": self.sauce_labs_username, "access_key": self.sauce_labs_access_key,
                                    "tunnelIdentifier": running_tunnel})
                elif browser.get(c.USE_SAUCE_LABS) and not running_tunnel:
                    error_list.append("Unable to find a usable Sauce Labs tunnel. Due to this, the requested "
                                      "screenshot job was completed using Firefox on the running Hippo Prod service.")

                site_paths = self.gather_urls(site_paths, url, project, browser, skip_sections, site_sections,
                                              project_config, self.username, self.password)
            except Exception as e:
                message = "An error was caught while crawling the site | {e}"
                raise c.HippoThreadError(message, stacktrace=traceback.format_exc())

            log.info("Preparing to capture {} screenshots of {} page(s) with "
                     "{} thread(s) on {}.".format("Desktop" if not mobile else "Mobile",
                                                  len(site_paths), thread_count, sanitized_url))

            # - Create image_list
            image_list = c.add_urls_to_image_list(image_list, user, project, branch, sanitized_url, site_paths,
                                                  build_id, mobile, browser, self.content_path)

            paginated, footers, headers, browser_size, before_screenshot, scroll_padding, \
                content_container_selector = self.parse_screenshot_thread_data(project_config, mobile, project,
                                                                               browser_size)

            if requested_pagination is not None:
                paginated = requested_pagination

            common_actions, mobile_actions, desktop_actions, reference_actions = self.parse_action_data(project_config)

            # - Create screenshot threads
            for i in range(thread_count):
                sc_thread = ScreenshotThread(screenshot_queue, self.s3, s3_image_path, local_image_path, project_config,
                                             project, url, image_list, browser, self.content_path, scroll_padding,
                                             footers, headers, before_screenshot, browser_size, paginated,
                                             custom_inputs, common_actions, desktop_actions, mobile_actions,
                                             action_libraries, reference_actions, error_list, self.username,
                                             self.password, self.pfizer_username, self.pfizer_password, self.pfizer_url,
                                             content_container_selector, mobile, file_extension, resize_delay=1)
                sc_thread.setDaemon(True)
                sc_thread.start()
                screenshot_thread_list.append(sc_thread)

            # - Add the pages to be captured to the queue for the threads to begin capturing
            for page_object in image_list["image_list"]:
                screenshot_queue.put(page_object)

            # - Wait for all of the threads to finish their tasks
            for t in screenshot_thread_list:
                t.join()

            try:
                # - Create and send the pdf
                # Instantiate the pdf creator class
                log.info("Starting PDF generation process....")
                pdf = pdf_creator.PDFCreator(image_list, self.s3, s3_image_path)
                pdf_url, pdf_image_list = pdf.create_pdf(local_image_path, f"{requested_project}_{('Mobile' if mobile else 'Desktop')}_screenshots.pdf", file_extension)
                log.info(f"PDF created successfully!: {pdf_url}")
                # Add pdf url to the image_list(s)
                image_list["pdf_url"] = pdf_url
                pdf_image_list["pdf_url"] = pdf_url

                # Send the full page image list up to S3 and store its url in the pdf list
                image_list_url = self._send_image_list_to_s3(image_list, s3_image_path, "falcon_image_list.json")
                pdf_image_list["falcon_image_list"] = image_list_url

            except Exception as e:
                message = f"Error while creating/Sending the pdf | {e}"
                log.error(message)
                error_list.append(message)
                pass

        except c.HippoGeneralException as hippo_error:
            message = f"An exception occurred within Hippo while performing this run, causing the job to be " \
                      "cancelled | {hippo_error}"
            log.error(message)
            error_list.append(message)

        except Exception as e:
            message = f"Unexpected exception occurred when attempting to process request: {request_data}. \n" \
                      "Exception: {e}"
            log.error(message)
            error_list.append(message)

        # - Create and send log to Rhino and Email
        self._output_screenshot_log(requested_project, sanitized_url, branch, send_to_rhino, build_id, user,
                                    pdf_image_list, error_list, s3_image_path, recipients, request_data["start_date"],
                                    request_data["start_time"], site_sections, skip_sections)

        # Delete local screenshot folder
        try:
            log.info("Deleting the temp folder that stored the images during this run.")
            shutil.rmtree(local_image_path)
        except Exception:
            log.info("The local screenshot folder path never got created. Could not delete it.")

        log.info(f"Ending screenshot request for {requested_project} - {branch}")

    def parse_request_data(self, request_data):
        requested_project = request_data[c.PROJECT].lower()
        branch = request_data.get(c.BRANCH, c.DEFAULT_BRANCH)
        send_to_rhino = request_data.get(c.SEND_TO_RHINO)
        # Remove the path from the domain to get the Base_url or the site
        url = c.parse_base_url(request_data[c.URL])
        browser = request_data.get(c.BROWSER, c.DEFAULT_BROWSER)
        browser_size = request_data.get(c.BROWSER_SIZE, None)
        user = request_data[c.USER]
        build_id = request_data[c.BUILD_ID]
        # Check whether urls were provided with the request and use those
        internal_urls = request_data.get(c.SITE_PATHS)
        site_sections = request_data.get(c.SITE_SECTIONS, [])
        skip_sections = request_data.get(c.SKIP_SECTIONS, [])
        mobile = request_data.get(c.MOBILE_ENVIRONMENT, False)
        file_extension = request_data.get(c.FILE_EXTENSION_PARAMETER, c.JPEG_FILE_EXTENSION)
        local_path = request_data.get(c.LOCAL_CONFIG_PATH)
        recipients = request_data.get(c.RECIPIENTS, None)
        requested_pagination = request_data.get(c.PAGINATED, None)
        custom_inputs = request_data.get(c.CUSTOM_INPUTS, None)
        
        logging.info(f"Parsing request data for {requested_project}")

        return requested_project, branch, send_to_rhino, url, browser, browser_size, user, build_id, internal_urls, site_sections, \
            skip_sections, mobile, file_extension, local_path, recipients, custom_inputs, requested_pagination

    def get_configuration(self, project, branch, local_path=None):
        config_filename = f"{project}_{branch}.json"
        project_config = None

        # - Grab the config from a local path if provided
        # If an absolute path directly to the file was given, use that one!
        if local_path:
            with open(local_path) as json_file:
                project_config = json.load(json_file)
        elif self.github_directory and self.environment in ["local"]:
            # - If you're running local and have specified a github directory for the local configs, look for it there
            # Gather a list of all files in the given directory
            config_files = [f for f in os.listdir(self.github_directory + "/sites")
                            if os.path.isfile(os.path.join(self.github_directory + "/sites", f))]

            config_path = f"{self.github_directory}/sites/{config_filename}"

            # Open the config file if it exists
            if os.path.exists(config_path):
                with open(config_path) as json_file:
                    project_config = json.load(json_file)

        # - Look up on github if a local file was not available
        if not project_config:
            project_config = c.get_configuration_from_github(project, branch, self.environment, self.github_token, self.repo)

        # - Validate that the configuration matches the schema
        if project_config:
            validate_project_config(project_config)

        return project_config

    def get_action_libraries(self):
        action_dict = {}

        if self.github_directory and self.environment in ["local"]:
            local_action_path = self.github_directory + "/action_libraries"
            config_files = [f for f in os.listdir(local_action_path)
                            if os.path.isfile(os.path.join(local_action_path, f))]
            for file_name in config_files:
                if file_name.endswith(".json"):
                    with open(f"{local_action_path}/{file_name}") as action_library:
                        action_dict[file_name.rstrip(".json")] = json.load(action_library)

        # - Get actions libraries for GitHub
        else:
            headers = {"Authorization": f"token {self.github_token}"}

            # Get a list of all action libraries available for Hippo (on this environment's branch)
            action_libraries = c.get_config_list(self.repo, self.github_branch, "action_libraries", headers)

            # - Request the config data
            for library in action_libraries:

                repo_path = f"/meltmedia/{self.repo}/{self.github_branch}/action_libraries/{library}"
                resp = requests.get(f"https://raw.githubusercontent.com{repo_path}", headers=headers)
                # Check that the respone had a good status code
                if resp.status_code > 400:
                    message = f"A bad status code of {resp.status_code} was returned when attempting to grab the action library at {repo_path}. " \
                              "Please see your QA rep for help troubleshooting this issue: {resp.text}"
                    log.error(message)
                    raise c.HippoGeneralException(message)
                else:
                    library_name = library.rstrip(".json")
                    library_content = json.loads(resp.content)
                    action_dict[library_name] = library_content

        return action_dict

    def gather_urls(self, site_paths, url, project, browser, skip_sections, site_sections, config, username, password):
        # - Gather urls for the site
        # Check whether urls were provided within the project config and use those
        if not site_paths:
            site_paths = config.get(c.SITE_PATHS)

        # - Otherwise, crawl the sitemap
        if not site_paths:
            # Get sitemap url
            if config.get(c.SITEMAP_PATH):
                sitemap_url = url + config[c.SITEMAP_PATH]
            else:
                sitemap_url = c.get_sitemap_path(project, config, url, self.content_path)

            # Crawl the sitemap_url for the internal urls for this site
            site_paths = c.crawl(sitemap_url, browser, url, username, password, self.content_path)
            # TODO: These site path are full URLs at this point

            # - Add the hidden pages of the site to the url list, if there are any specified in the config
            for page in config.get(c.HIDDEN_PAGES, []):
                site_paths.append(page)

        # Add any skip sections from the project config to the skip sections list
        skip_sections = skip_sections + config.get(c.SKIP_SECTIONS, [])

        # - Remove sections and pages that are not specified to be captured this screenshot run
        site_paths = c.trim_sections(site_paths, self.content_path, site_sections, skip_sections)

        return site_paths

    def parse_screenshot_thread_data(self, config, mobile, project, browser_size):
        try:
            # - Instantiate variables for cases where there is neither a desktop or mobile environment
            paginated = False
            footers = []
            headers = []
            config_browser_size = None
            before_screenshot = None
            scroll_padding = DEFAULT_SCROLL_PADDING
            content_container_selector = "html"

            # - Set Up Environment variables
            # Set any common attributes
            environments = config.get(c.ENVIRONMENTS, {})
            common_config = environments.get(c.COMMON_ENVIRONMENT)
            if common_config:
                paginated = common_config.get(c.PAGINATED, paginated)
                footers = common_config.get(c.FOOTERS, footers)
                headers = common_config.get(c.HEADERS, headers)
                config_browser_size = common_config.get(c.BROWSER_SIZE, config_browser_size)
                scroll_padding = common_config.get(c.SCROLL_PADDING_KEY, scroll_padding)
                before_screenshot = common_config.get(c.BEFORE_SCREENSHOT_KEY, before_screenshot)
                content_container_selector = common_config.get(c.CONTENT_CONTAINER_SELECTOR_KEY,
                                                               content_container_selector)

            # Overwrite environment parameters if they exist in the Mobile or Desktop environments
            if mobile:
                mobile_config = environments.get(c.MOBILE_ENVIRONMENT)
                config_browser_size = c.DEFAULT_MOBILE_BROWSER_SIZE if not config_browser_size else config_browser_size
                if mobile_config:
                    paginated = mobile_config.get(c.PAGINATED, paginated)
                    footers = mobile_config.get(c.FOOTERS, footers)
                    headers = mobile_config.get(c.HEADERS, headers)
                    config_browser_size = mobile_config.get(c.BROWSER_SIZE, config_browser_size)
                    scroll_padding = mobile_config.get(c.SCROLL_PADDING_KEY, scroll_padding)
                    before_screenshot = mobile_config.get(c.BEFORE_SCREENSHOT_KEY, before_screenshot)
                    content_container_selector = mobile_config.get(c.CONTENT_CONTAINER_SELECTOR_KEY,
                                                                   content_container_selector)
            else:
                desktop_config = environments.get(c.DESKTOP_ENVIRONMENT)
                config_browser_size = c.DEFAULT_DESKTOP_BROWSER_SIZE if not config_browser_size else config_browser_size
                if desktop_config:
                    paginated = desktop_config.get(c.PAGINATED, paginated)
                    footers = desktop_config.get(c.FOOTERS, footers)
                    headers = desktop_config.get(c.HEADERS, headers)
                    config_browser_size = desktop_config.get(c.BROWSER_SIZE, config_browser_size)
                    scroll_padding = desktop_config.get(c.SCROLL_PADDING_KEY, scroll_padding)
                    before_screenshot = desktop_config.get(c.BEFORE_SCREENSHOT_KEY, before_screenshot)
                    content_container_selector = desktop_config.get(c.CONTENT_CONTAINER_SELECTOR_KEY,
                                                                    content_container_selector)

            # Set the browser size to the requested values, if one was provided
            if browser_size:
                # Use thte width/height from the request if available, otherwise retain the value from the config
                width = browser_size.get(c.WIDTH_KEY)
                height = browser_size.get(c.HEIGHT_KEY)

                # Make sure a None or 0 value is not accepted
                if not width:
                    width = config_browser_size[c.WIDTH_KEY]
                if not height:
                    height = config_browser_size[c.HEIGHT_KEY]
                browser_size = {c.WIDTH_KEY: width, c.HEIGHT_KEY: height}
            else:
                browser_size = config_browser_size

            if all(env not in environments.keys() for env in [c.MOBILE_ENVIRONMENT, c.DESKTOP_ENVIRONMENT]):
                log.warn(f"This project's configuration file does not have a {c.DESKTOP_ENVIRONMENT!r} or {c.MOBILE_ENVIRONMENT} environment.")

            return paginated, footers, headers, browser_size, before_screenshot, scroll_padding, \
                   content_container_selector

        except KeyError as key:
            message = f"The key {key} is missing from the config data"
            raise c.MissingKey(message, key, stacktrace=traceback.format_exc(),
                               details={"missing_key": str(key)})

        except Exception as e:
            # Catch all messages coming in and format the message to include the setup method location
            message = "Problem encountered while gathering the environment variables for the run: {e}"
            raise c.HippoThreadError(message, stacktrace=traceback.format_exc())

    def parse_action_data(self, config):
        common_actions = {}
        mobile_actions = {}
        desktop_actions = {}
        reference_actions = {}

        # - Parse out the different actions by environment
        try:
            environments = config.get(c.ENVIRONMENTS, {})

            if c.COMMON_ENVIRONMENT in environments:
                for page in environments[c.COMMON_ENVIRONMENT].get(c.PAGES, []):
                    if type(page[c.PATH_KEY]) is list:
                        for path in page[c.PATH_KEY]:
                            common_actions[path] = page[c.ACTION_LIST_KEY]
                    else:
                        common_actions[page[c.PATH_KEY]] = page[c.ACTION_LIST_KEY]

            if c.MOBILE_ENVIRONMENT in environments:
                for page in environments[c.MOBILE_ENVIRONMENT].get(c.PAGES, []):
                    if type(page[c.PATH_KEY]) is list:
                        for path in page[c.PATH_KEY]:
                            mobile_actions[path] = page[c.ACTION_LIST_KEY]
                    else:
                        mobile_actions[page[c.PATH_KEY]] = page[c.ACTION_LIST_KEY]

            if c.DESKTOP_ENVIRONMENT in environments:
                for page in environments[c.DESKTOP_ENVIRONMENT].get(c.PAGES, []):
                    if type(page[c.PATH_KEY]) is list:
                        for path in page[c.PATH_KEY]:
                            desktop_actions[path] = page[c.ACTION_LIST_KEY]
                    else:
                        desktop_actions[page[c.PATH_KEY]] = page[c.ACTION_LIST_KEY]

            if c.REFERENCE_ENVIRONMENT in environments:
                for page in environments[c.REFERENCE_ENVIRONMENT].get(c.PAGES, []):
                    if type(page[c.PATH_KEY]) is list:
                        for path in page[c.PATH_KEY]:
                            reference_actions[path] = page[c.ACTION_LIST_KEY]
                    else:
                        reference_actions[page[c.PATH_KEY]] = page[c.ACTION_LIST_KEY]

            return common_actions, mobile_actions, desktop_actions, reference_actions

        except KeyError as key:
            message = f"The key {key!r} was missing from the config data while parsing the action lists"
            raise c.MissingKey(message, key, stacktrace=traceback.format_exc(), details={"missing_key": str(key)})

        except Exception as e:
            message = f"Unexpected error while parsing the action list | {e}"
            raise c.HippoThreadError(message, stacktrace=traceback.format_exc())

    def _output_screenshot_log(self, project, url, branch, send_to_rhino, build_id, user, image_list, error_list,
                               image_path, recipients, start_date, start_time, site_sections, skip_sections):
        """Handles output creation of the form submissions
        :param
            - 'name':           String name of the form under test
            - 'submissions':    Array of submissions
        """
        try:
            # Determine the run status based on number of errors retrieved
            result = c.FAILED if error_list else c.PASSED

            # Remove duplicate errors from the error list for a cleaner log file
            error_list = list(set(error_list))

            # If the screenshot job fails, always send to jhabinder.sharma@growthnatives.com
            if result == c.FAILED:
                recipients.append("jhabinder.sharma@growthnatives.com")

            log.info("Generating the log file")

            log.info(f"Generating the {c.LOG_FILENAME} file")

            # Remove The Miscellaneous page if it doesn't have any image
            misc_page = image_list["image_list"][-1]
            if not misc_page["image_data"]:
                image_list["image_list"].pop(-1)

            # import pdb; pdb.set_trace()
            # Add the log path to the image_list
            image_list[c.SCREENSHOT_LOG_URL] = f"http://{self.s3_bucket}.s3.amazonaws.com/{(self.s3._generate_file_path(image_path, c.LOG_FILENAME))}"

            # Send the image_list up to S3
            image_list_url = self._send_image_list_to_s3(image_list, image_path, "pdf_image_list.json")
            image_list[c.IMAGE_LIST_URL] = image_list_url
            log.info(f"Image List JSON: {image_list_url}")
            try:
                # - Create and send log file
                screenshot_log = c.create_html_log(image_list, result, start_date, start_time, error_list,
                                                   site_sections, skip_sections)
                screenshot_log_path = self.s3.store_file(image_path, screenshot_log, c.LOG_FILENAME, True)
                log.info(f"Screenshot log: {screenshot_log_path}")

            except S3ClientException as s3_exception:
                log.error(f"Unable to connect or post {c.LOG_FILENAME!r} form results to S3 for project {project!r}: {s3_exception.msg!r}")
                raise s3_exception

            job_link = None
            if send_to_rhino:
                try:
                    job_link = f"http://{self.rhino_host}/#/brand/{project}/branch/{branch}/build/{build_id}"
                    c.send_job_to_rhino(project, url, branch, user, build_id, screenshot_log_path, result, self.rhino_host,
                                        job_link)
                except RhinoClientException as rhino_exception:
                    log.error(f"Unable to post screenshot results for {project} Rhino for project : {rhino_exception.msg}")
                    raise rhino_exception

            try:
                if recipients and self.mandrill_key:
                    log.info("Attempting to send results email to the given recipients")

                    if job_link:
                        c.send_emails(self.mandrill_key, project, url, branch, screenshot_log_path, result, recipients, job_link)
                    else:
                        c.send_emails(self.mandrill_key, project, url, branch, screenshot_log_path, result, recipients)

                    log.info("Email sent successfully!")
            except EmailClientException as email_exception:
                log.error(f"Unable to send screenshot results email for {project} : {email_exception.msg}")
                raise email_exception

        except Exception as e:
            log.error(f"Unexpected error occurred when attempting to output {c.LOG_FILENAME!r} screenshot results for project {project!r}: {e.message}")
            raise e

    def _send_image_list_to_s3(self, image_list, image_path, filename):
        image_list_file = BytesIO()
        image_list_file.write(bytes(json.dumps(image_list), encoding="utf-8"))
        image_list_file.seek(0)
        return self.s3.store_file(image_path, image_list_file, filename, True)
