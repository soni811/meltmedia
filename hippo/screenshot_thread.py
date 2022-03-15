from hippo import actions
import threading
import time
import traceback
import hippo.util as c
from src.the_ark.selenium_helpers import SeleniumHelpers, DriverExceptions, DriverURLError, TimeoutError
from src.the_ark.screen_capture import Screenshot, ScreenshotException
from src.the_ark.selenium_helpers import SeleniumHelperExceptions

log = c.create_logger("Screenshot Thread")
DEFAULT_SCREENSHOT_THREAD_COUNT = 4


class ScreenshotThread(threading.Thread):
    def __init__(self, screenshot_queue, s3_client, s3_path, local_path, config, project, base_url, image_lists,
                 desired_capabilities, content_path, padding, footers, headers, before_screenshot, browser_size,
                 paginated, custom_inputs, common_actions, desktop_actions, mobile_actions, action_libaries,
                 reference_actions, error_list, username, password, pfizer_username, pfizer_password, pfizer_url,
                 content_container_selector="html", mobile=False, file_extension=c.JPEG_FILE_EXTENSION, resize_delay=0):
        threading.Thread.__init__(self)
        self.url_queue = screenshot_queue
        self.s3_client = s3_client
        self.s3_path = s3_path
        self.local_path = local_path
        self.config = config
        self.project = project
        self.base_url = base_url
        self.image_lists = image_lists
        self.desired_capabilities = desired_capabilities
        self.is_mobile = mobile
        self.error_list = error_list
        self.sc = None
        self.sh = None
        self.image_list_object = {}
        self.path = ""
        self.author = False
        self.dispatch = False
        self.file_extension = file_extension
        self.resize_delay = resize_delay

        self.paginated = paginated
        self.footers = footers
        self.headers = headers
        self.before_screenshot = before_screenshot
        self.content_container_selector = content_container_selector

        self.scroll_padding = padding
        self.content_path = content_path
        self.common_actions = common_actions
        self.desktop_actions = desktop_actions
        self.mobile_actions = mobile_actions
        self.action_libraries = action_libaries
        self.reference_actions = reference_actions
        self.browser_size = browser_size
        self.custom_inputs = custom_inputs

        self.username = username
        self.password = password

        self.pfizer_username = pfizer_username
        self.pfizer_password = pfizer_password
        self.pfizer_url = pfizer_url

        self.ac = None

    def run(self):
        try:
            self.setup()
            while not self.url_queue.empty():
                self.image_list_object = {}
                test_url = None
                try:
                    self.image_list_object = self.url_queue.get()

                    self.path = self.image_list_object["path"]

                    test_url = self.image_list_object["url"]

                    # Do not try and load or capture the miscellaneous images page
                    if test_url == c.MISC_PATH_TEXT:
                        continue

                    self.load_url(test_url)
                    time.sleep(5)

                    c.close_iperceptions(self.sh)

                    if self.config.get("platform"):
                        c.close_gene_cookie_modal(self.sh)

                    # - Perform the Before Screenshot actions for this site
                    try:
                        # Confirm that there are actions to take
                        if self.before_screenshot:
                            # Check that the current path is not excluded and skip the action if it is
                            if self.path not in self.before_screenshot.get(c.PATHS_TO_SKIP_KEY, []):
                                self.dispatch_actions(self.before_screenshot[c.ACTION_LIST_KEY])
                            else:
                                log.info(f"Skipping the Before Screenshot Actions on {self.path!r}")
                    except SeleniumHelperExceptions as selenium_error:
                        log.debug(f"Unable to perform the Before Screenshot actions on {self.path!r} due to: {selenium_error.msg}")
                    except Exception as e:
                        log.error(f"Unexpected error occurred while performing the Before Screenshot Actions on {test_url!r}: {e}")

                    # - Path not in any environment
                    if all(self.path not in path_list for path_list in [self.common_actions,
                                                                        self.desktop_actions,
                                                                        self.mobile_actions]):
                        self.launch_capture()

                    # - On desktop, but path not specified for desktop
                    elif not self.is_mobile and self.path not in self.common_actions and self.path \
                            not in self.desktop_actions:
                        self.launch_capture()

                    # - On mobile, but path not specified for mobile
                    elif self.is_mobile and self.path not in self.common_actions and self.path \
                            not in self.mobile_actions:
                        self.launch_capture()

                    # - Otherwise, perform the actions specified for the environment
                    else:
                        if self.path in self.common_actions:
                            self.dispatch_actions(self.common_actions[self.path])

                        if self.is_mobile and self.path in self.mobile_actions:
                            self.dispatch_actions(self.mobile_actions[self.path])
                        elif not self.is_mobile and self.path in self.desktop_actions:
                            self.dispatch_actions(self.desktop_actions[self.path])

                except ScreenshotException as screen_error:
                    message = f"Screenshot Exception caught while capturing for the page at {test_url!r} | "
                    screen_error.msg = f"{message}{screen_error.msg}"
                    log.error(screen_error)
                    self.error_list.append(screen_error.msg)

                except SeleniumHelperExceptions as selenium_error:
                    message = f"Selenium Exception caught while capturing for the page at {test_url!r} | "
                    selenium_error.msg = f"{message}{selenium_error.msg}"
                    log.error(selenium_error)
                    self.error_list.append(selenium_error.msg)

                except DriverURLError as e:
                    message = f"The browser timed out while attempting to load a page while running actions for {test_url} . " \
                              "Please check with your Hippo representative that this URL has been configured " \
                              f"| {e.message}"
                    log.error(message)
                    self.error_list.append(message)

                except Exception as e:
                    message = f"An Unexpected Error popped up while capturing for the page at {test_url!r} | {e}"
                    log.error(message + traceback.format_exc())
                    self.error_list.append(message)

                finally:
                    self.url_queue.task_done()

        except ScreenshotException as e:
            log.error(e)
            self.error_list.append(e.msg)

        except Exception as e:
            log.error(e)
            self.error_list.append(str(e))

        finally:
            self.kill()

    def setup(self):
        log.debug("Starting Screenshot Thread Setup")
        try:
            self.sh = SeleniumHelpers()
            self.sh.create_driver(**self.desired_capabilities)
            # self.sh.driver.set_page_load_timeout(30)
        except DriverExceptions as driver_error:
            driver_error.msg = f"Could not create the selenium driver | {driver_error.msg}"
            raise driver_error

        try:
            log.info("Checking for Author environment")
            self.load_url(self.base_url)
            current_url = self.sh.get_current_url()
            if self.config.get(c.PFIZER) or c.check_if_author(self.base_url) or c.check_if_dispatch(self.base_url) or any(indicator in current_url for indicator in c.GENE_SAML_LOGIN_INDICATOR):
                self.authenticate_driver()
            else:
                self.load_url(self.base_url)

            self.start_screenshot_class()

        except Exception as e:
            # TODO: Find a way to determine if all of the threads failed so that the log can tell the user.
            message = f"Unable to authenticate the driver for this thread: {e}"
            log.warning(message)
            raise c.HippoGeneralException(message)

    def start_screenshot_class(self):
        log.debug("Starting Screenshot Class")
        try:
            self.sc = Screenshot(selenium_helper=self.sh, paginated=self.paginated, header_ids=self.headers,
                                 footer_ids=self.footers, scroll_padding=self.scroll_padding,
                                 file_extenson=self.file_extension, content_container_selector=self.content_container_selector, resize_delay=self.resize_delay)



            # - Resize browser if a size has been specified
            if self.browser_size and not self.desired_capabilities.get(c.MOBILE_ENVIRONMENT, False):
                log.info("Resizing browser")
                self.sh.resize_browser(self.browser_size[c.WIDTH_KEY], self.browser_size[c.HEIGHT_KEY])

            # - Instantiate the Action Class to be used for this thread
            self.ac = actions.Action(self, self.sh, self.custom_inputs, self.scroll_padding)

        except KeyError as key:
            message = f"The key {key} is missing from the config data"
            raise c.MissingKey(message, key, stacktrace=traceback.format_exc(),
                               details={"missing_key": str(key)})
        except Exception as e:
            error_text = e.msg if hasattr(e, 'msg') else e
            # Catch all messages coming in and format the message to include the setup method location
            message = f"Problem encountered while gathering the environment variables for the run: {error_text}"
            raise c.HippoThreadError(message, stacktrace=traceback.format_exc())

    def authenticate_driver(self):
        # Navigate the browser to the base url, log in, and set the browser to the environment's settings
        log.info("Authenticating Driver")
        try:
            # - Determine whether the run is happening on an author environment
            # if the domain starts with the author site indicator
            if self.config.get(c.PLATFORM):
                self.author = c.check_if_author(self.base_url)
            # Log in to the site if needed. This also loads the base url
            if self.author:
                with threading.Lock():
                    c.platform_login(self.sh, self.base_url, self.username, self.password)
                    if "author" in self.base_url:
                        log.debug("Logging into an Author environment")
                        # Ensuring that the AEM author (https://author.aem.gene.com/aem/start.html) is loading properly.
                        self.sh.wait_for_element(css_selector=".globalnav-homecard [icon='project']")
                    else:
                        # Ensuring that the site loads in the UAT dispatcher environment. 
                        log.debug("Logging into a UAT dispatcher environment")
                        self.sh.wait_for_element(css_selector="[href*='www.gene.com']")

            else:
                log.debug("Non-Author environment login initiated")
                with threading.Lock():
                    c.platform_login(self.sh, self.base_url, self.username, self.password)

            # Authenticate Pfizer development environments
            with threading.Lock():
                if self.config.get(c.PFIZER):
                    if "www" not in self.base_url:
                        if self.pfizer_username and self.pfizer_password and c.PFIZER_AUTH_URL_LIST:
                            # TODO: Work with Drew to build a cred key group for these sites
                            # - Authenticate against the Pfizer copay card site urls
                            for auth_url in c.PFIZER_AUTH_URL_LIST:
                                c.authenticate_browser(self.sh, auth_url, self.pfizer_username, self.pfizer_password)
                        else:
                            log.warning("Could not authenticate this Pfizer site because either the username, password,"
                                        " or authentication url were not present in the app configuration")

            # Load the base url to ensure the site is accessible
            self.load_url(self.base_url)
            time.sleep(5)
            # Verify that the browser was able to navigate past the new tab screen and auth popup
            if "@" in self.base_url:
                base_url = self.base_url.split("@")[1]
            else:
                base_url = self.base_url

            if base_url not in self.sh.get_current_url():
                message = "Page was not authenticated"
                raise ScreenshotException(message)

        except ScreenshotException as e:
            message = "Hippo was unable to set up your browser - The browser did not pass the new tab screen when " \
                      f"attempting to authenticate the requested site at {c.remove_basic_auth(self.base_url)} . Please check with your Hippo " \
                      f"representative that this URL has been configured | {e.msg}"
            raise ScreenshotException(message)
        except DriverURLError as e:
            message = "Hippo was unable to set up your browser - The browser timed out while attempting to " \
                      f"authenticate the requested site at {c.remove_basic_auth(self.base_url)} . Please check with your Hippo representative that this " \
                      f"URL has been configured | { e.msg}"
            raise ScreenshotException(message, stacktrace=traceback.format_exc())
        except Exception as e:
            error_text = e.msg if hasattr(e, 'msg') else e
            message = f"An Unexpected error occurred while attempting to log in to the requested site | {error_text}"
            raise ScreenshotException(message, stacktrace=traceback.format_exc())

    def load_url(self, url):
        # Add Authentication if provided
        if self.config.get(c.PFIZER):
            self.sh.load_url(c.get_test_url(url, self.pfizer_username, self.pfizer_password),
                             bypass_status_code_check=True)
        else:
            self.sh.load_url(url, bypass_status_code_check=True)
            time.sleep(5)

    def dispatch_actions(self, actions_list, element=None):
        action_type = ""
        try:
            for action in actions_list:
                action_type = action[c.ACTION_KEY]

                # Dispatch the action to the appropriate method in the Action Class
                try:
                    getattr(self.ac, action_type)(action, element)
                except c.HippoGeneralException as actions_error:
                    log.warning(f"An error occurred while performing a {action_type!r} action on the {self.path} | {actions_error}")

        except AttributeError as attr_error:
            message = f"An AttributeError Exception was raised while performing a {action_type} action! Check the spelling " \
                      "of the action and ask your Hippo admin to update the configuration schema to include a check " \
                      f"for the proper naming of this action. Error: {attr_error}"
            log.error(message)
            self.error_list.append(message)

        except KeyError as key_error:
            message = f"A KeyError Exception for the key named {key_error!r} was raised while performing a {action_type} action! " \
                      "Check the spelling of the key and ask your Hippo admin to update the configuration schema" \
                      "to include a check for the proper key's existence"
            log.error(message)
            self.error_list.append(message)

        except SeleniumHelperExceptions as selenium_error:
            message = f"Encountered a Selenium Exception while performing a {action_type!r} action | "
            selenium_error.msg = "{0}{1}".format(message, selenium_error.msg)
            raise selenium_error

    def dispatch_external_reference(self, action, reference):
        try:
            library = action[c.LIBRARY_KEY]
            action_list = self.action_libraries[library].get(reference)
            if action_list:
                self.dispatch_actions(action_list)
            else:
                log.info(f"The external Library {library!r} you are trying to access does not contain an action list named {reference}!")
        except KeyError as key_error:
            log.warning(f"Please see Hippo Admin. There is an issue with the action library named: {key_error}")
        except ImportError as import_error:
            log.warning(
                f"Please see Hippo Admin. Unable to find action library named {library!r} | {import_error}")

    def launch_capture(self, full_name="", current_url=False, suffix="", viewport_only=False, padding=None,
                       add_to_misc=False):
        # - Get the image file(s)
        image_file = self.sc.capture_page(viewport_only, padding)
        # import pdb; pdb.set_trace();
        if full_name:
            # - If a list of images was returned, send each image in the list
            if type(image_file) is list:
                for index, image in enumerate(image_file):
                    # - Iterate the image name
                    new_suffix = f"{suffix}_00{(index + 1)}" if suffix else (f'{(index + 1)}')
                    self._handle_image(image, full_name=full_name, suffix=new_suffix, add_to_misc=add_to_misc)
            else:
                # - Send the image off to S3 and store it's location in the image_list for the captured page
                self._handle_image(image_file, full_name=full_name, suffix=suffix, add_to_misc=add_to_misc)

        elif current_url:
            # - If a list of images was returned, send each image in the list
            if type(image_file) is list:
                for index, image in enumerate(image_file):
                    # - Iterate the image name
                    new_suffix = f"{suffix}_{(index + 1)}" if suffix else (f"{(index + 1)}")
                    self._handle_image(image, current_url=current_url, suffix=new_suffix, add_to_misc=add_to_misc)
            else:
                # - Send the image off to S3 and store it's location in the image_list for the captured page
                self._handle_image(image_file, current_url=current_url, suffix=suffix, add_to_misc=add_to_misc)

        elif suffix:
            # - If a list of images was returned, send each image in the list
            if type(image_file) is list:
                for index, image in enumerate(image_file):
                    # - Iterate the image name
                    new_suffix = f"{suffix}_{(index + 1)}" if suffix else (f"{(index + 1)}")
                    self._handle_image(image, suffix=new_suffix, add_to_misc=add_to_misc)
            else:
                # - Send the image off to S3 and store it's location in the image_list for the captured page
                self._handle_image(image_file, suffix=suffix, add_to_misc=add_to_misc)

        else:
            # - If a list of images was returned, send each image in the list
            if type(image_file) is list:
                for index, image in enumerate(image_file):
                    # - Iterate the image name
                    new_suffix = f"{suffix}_{(index + 1)}" if suffix else (f"{(index + 1)}")
                    self._handle_image(image, full_name="", suffix=new_suffix, add_to_misc=add_to_misc)
            else:
                # - Send the image off to S3 and store it's location in the image_list for the captured page
                self._handle_image(image_file, add_to_misc=add_to_misc)

    def launch_capture_scrolling_element(self, css_selector, full_name="", suffix="", current_url=False,
                                         scroll_padding=None, viewport_only=True, add_to_misc=False):
        padding = scroll_padding or self.scroll_padding

        # - Capture the images
        image_files = self.sc.capture_scrolling_element(css_selector, viewport_only, padding)

        # - Send each image up to S3 and store it's location in the image_list for the captured page
        for index, image in enumerate(image_files):
            if full_name:
                if suffix:
                    full_image_name = f"{full_name}_{suffix}_{(index + 1)}"
                    self._handle_image(image, full_image_name, add_to_misc=add_to_misc)
                else:
                    full_image_name = f"{full_name}_{(index + 1)}"
                    self._handle_image(image, full_image_name, add_to_misc=add_to_misc)
            elif current_url:
                new_base_filename = c.get_screenshot_name(self.sh.get_current_url())
                if suffix:
                    full_image_name = f"{new_base_filename}_{suffix}_{(index + 1)}"
                    self._handle_image(image, full_name=full_image_name, add_to_misc=add_to_misc)
                else:
                    full_image_name = f"{new_base_filename}_{(index + 1)}"
                    self._handle_image(image, full_name=full_image_name, add_to_misc=add_to_misc)
            elif suffix:
                new_suffix = f"{suffix}_{(index + 1)}"
                self._handle_image(image, suffix=new_suffix, add_to_misc=add_to_misc)
            else:
                new_suffix = f"{(index + 1)}"
                self._handle_image(image, suffix=new_suffix, add_to_misc=add_to_misc)

    def _handle_image(self, image_file, full_name="", current_url=False, suffix="", add_to_misc=False):
        # TODO: Update once the image name creator is in the ark
        # - Create the image name
        image_name_base = c.get_screenshot_name(self.path)
        if full_name:
            if suffix:
                image_name = f"{full_name}_{suffix}.{self.file_extension}"
            else:
                image_name = f"{full_name}.{self.file_extension}"

        elif current_url:
            current_url_base = self.sh.get_current_url()
            new_url_base = c.get_screenshot_name(current_url_base)
            if suffix:
                image_name = f"{new_url_base}_{suffix}.{self.file_extension}"
            else:
                image_name = f"{new_url_base}.{self.file_extension}"

        elif suffix:
            image_name_base = c.get_screenshot_name(self.path)
            if suffix:
                image_name = f"{image_name_base}_{suffix}.{self.file_extension}"
        else:
            image_name = f"{image_name_base}.{self.file_extension}"

        # - Send file to S3 and get its file location url
        image_file.seek(0)
        image_url = self.s3_client.store_file(self.s3_path, image_file, image_name, True)

        image_file.seek(0)
        c.save_stringIO_file_locally(self.local_path, image_name, image_file)

        # - Add the image to the image_lists under the page it was captured for
        # Create object with image data
        data_object = {"filename": image_name,
                       "suffix": suffix or "base_capture",
                       "s3_path": self.s3_path,
                       "s3_location": image_url,
                       "local_path": self.local_path + image_name,
                       "url": self.image_list_object["url"]}

        # Add the data to the image_list objects image_data list if add_to_misc is true
        if add_to_misc:
            self.image_lists["image_list"][-1]["image_data"].append(data_object)
        else:
            self.image_list_object["image_data"].append(data_object)

        # - Log the path so we can easily view the screenshot on S3
        log.info(f"Sent {image_name} to S3: {image_url}")

    def kill(self):
        if self.sh:
            self.sh.quit_driver()
