from asyncio.log import logger
import datetime
import json
import logging
import os
import re
import requests
import shutil
import time
import urllib3
from src.the_ark import selenium_helpers

from bs4 import BeautifulSoup
from github import Github
from io import StringIO
from src.the_ark.email_client import EmailClient
from src.the_ark.rhino_client import RhinoClient

from urllib.parse import urlparse

log = logging.getLogger("Hippo Utilities")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Genentech AEM Login Information
AUTHOR_SITE_INDICATOR = ["author", "dev-author", "uat", "author2"]
DISPATCH_INDICATOR = ["core"]
GENE_SAML_LOGIN_INDICATOR = ["gene.", "roche", "login", "wamua", "saml2"]

PFIZER_AUTH_URL_LIST = [
    # "https://pub-pfcopayoffers-stg.us2.digitalpfizer.com",
    "http://pub-pfcopayoffers-stg.digitalpfizer.com",
    "https://pub-pfcopayoffers-stg.digitalpfizer.com",
    "http://pfpharmalocstg.prod.acquia-sites.com"
]

MISC_PATH_TEXT = "Miscellaneous Images"
PDF_MAX_PAGE_HEIGHT = 19200.0
PDF_CROP_PADDING = 40

# App constants
S3_CONFIG_LOCATION = "configurations"
DEFAULT_BRANCH = "production"
RHINO_TEST_NAME = "Hippo Screenshot"
LOG_FILENAME = "screenshot_log.html"
SCREENSHOT_LOG_URL = "screenshot_log_url"
IMAGE_LIST_URL = "image_list_url"

# - Environment Variables
HIPPO_ENVIRONMENT = "HIPPO_ENVIRONMENT"
MANDRILL_KEY = "HIPPO_MANDRILL_KEY"
GRAYLOG_FACILITY = 'HIPPO_GRAYLOG_FACILITY'
GRAYLOG_LEVEL = 'HIPPO_GRAYLOG_LEVEL'
HIPPO_S3_BUCKET = 'HIPPO_S3_BUCKET'
RHINO_HOST = 'HIPPO_RHINO_HOST'
HIPPO_PORT = 'HIPPO_PORT'
GITHUB_REPO = 'GITHUB_REPO'
GITHUB_TOKEN = 'GITHUB_TOKEN'
GITHUB_DIRECTORY = 'GITHUB_DIRECTORY'
GITHUB_BRANCH = 'GITHUB_BRANCH'
ALLOW_BASE_CAPTURE = 'ALLOW_BASE_CAPTURE'
HIPPO_AEM_USERNAME = "HIPPO_AEM_USERNAME"
HIPPO_AEM_PASSWORD = "HIPPO_AEM_PASSWORD"
PFIZER_USERNAME = "PFIZER_USERNAME"
PFIZER_PASSWORD = "PFIZER_PASSWORD"
PFIZER_AUTH_URL = "PFIZER_AUTH_URL"
AWS_KEY = "AWS_ACCESS_KEY_ID"
AWS_SECRET = "AWS_SECRET_ACCESS_KEY"
WATERING_HOLE_CLIENT = "WATERING_HOLE_CLIENT"
SAUCE_LABS_USERNAME = "SAUCE_LABS_USERNAME"
SAUCE_LABS_ACCESS_KEY = "SAUCE_LABS_ACCESS_KEY"
HIPPO_SITES_PATH = "meltmedia/hippo-sites"

DEFAULT_APP_CONFIG = {
    HIPPO_ENVIRONMENT: "develop",
    RHINO_HOST: "growthnatives.com",
    HIPPO_PORT: 5001,
    HIPPO_S3_BUCKET: "qa-projects-gn",
    GITHUB_REPO: "GITHUB_REPO",
    GITHUB_BRANCH: "develop",
    ALLOW_BASE_CAPTURE: False,
    WATERING_HOLE_CLIENT: "meltmedia"
}

# - REQUEST KEYS
PROJECT = "project"
URL = "url"
BRANCH = "branch"
BROWSER = "browser"
USER = "user"
SEND_TO_RHINO = "send_to_rhino"
SITE_SECTIONS = "site_sections"
SKIP_SECTIONS = "skip_sections"
SITE_PATHS = "site_paths"
BUILD_ID = "build_id"
BROWSER_NAME = "browserName"
THREAD_COUNT = "thread_count"
LOCAL_CONFIG_PATH = "local_config_path"
PNG_FILE_EXTENSION = "png"
BMP_FILE_EXTENSION = "bmp"
JPEG_FILE_EXTENSION = "jpeg"
FILE_EXTENSION_PARAMETER = "file_extension"
STRING_IO_ONLY = "string_io_only"
RECIPIENTS = "recipients"
DEFAULT_BROWSER = {BROWSER_NAME: "phantomjs"}
START_DATE = "start_date"
START_TIME = "start_time"
HEADLESS = "headless"
BINARY = "binary"
WEBDRIVER = "webdriver"
SCALE_FACTOR = "scale_factor"
CROP_IMAGES_FOR_PDF = "crop_images_for_pdf"
USE_SAUCE_LABS = "use_sauce_labs"

# - CONFIG KEYS
COMMON_ENVIRONMENT = "common"
MOBILE_ENVIRONMENT = "mobile"
DESKTOP_ENVIRONMENT = "desktop"
REFERENCE_ENVIRONMENT = "reference"
BROWSER_SIZE = "browser_size"
HEADERS = "headers"
FOOTERS = "footers"
HIDDEN_PAGES = "hidden_pages"
SECURE_PAGES = "secure_pages"
PAGINATED = "paginated"
PLATFORM = "platform"
PFIZER = "pfizer"
ENVIRONMENTS = "environments"
SITEMAP_PATH = "sitemap_path"
PAGES = "pages"
BEFORE_SCREENSHOT_KEY = "before_screenshot"
CONTENT_CONTAINER_SELECTOR_KEY = "content_container_selector"
CONTENT_PATH = "content_path"
CUSTOM_INPUTS = "custom_inputs"
LABEL = "label"
DESCRIPTION = "description"
RESIZE_DELAY = "resize_delay"

# - Action Types:
CAPTURE_ACTION = "capture"
CAPTURE_SCROLLING_ELEMENT_ACTION = "capture_scrolling_element"
CAPTURE_ELEMENT_ACTION = "capture_element"
LOAD_URL_ACTION = "load_url"
CLICK_ACTION = "click"
CLICK_ELEMENT_WITH_OFFSET_ACTION = "click_element_with_offset"
HOVER_ACTION = "hover"
SCROLL_AN_ELEMENT_ACTION = "scroll_an_element"
REFRESH_ACTION = "refresh"
ENTER_TEXT_ACTION = "enter_text"
SEND_SPECIAL_KEY_ACTION = "send_special_key"
SLEEP_ACTION = "sleep"
WAIT_FOR_ELEMENT_ACTION = "wait_for_element"
SCROLL_WINDOW_TO_POSITION_ACTION = "scroll_window_to_position"
SCROLL_WINDOW_TO_ELEMENT_ACTION = "scroll_window_to_element"
REFERENCE_ACTION = "reference"
EXTERNAL_REFERENCE_ACTION = "external"
FOR_EACH_ACTION = "for_each"
SHOW_ELEMENT_ACTION = "show_element"
HIDE_ELEMENT_ACTION = "hide_element"
SWITCH_WINDOW_HANDLE_ACTION = "switch_window_handle"
SWITCH_WINDOW_IFRAME_ACTION = "switch_to_iframe"
CLOSE_WINDOW = "close_window"
EXECUTE_SCRIPT_ACTION = "execute_script"
FOCUS_ACTION = "focus"
RESIZE_BROWSER_ACTION = "resize_browser"
ADD_COOKIE_ACTION = "add_cookie"
DELETE_COOKIE_ACTION = "delete_cookie"

local_ = locals()
All_ACTION_TYPES = [local_[v] for v in dir() if v.endswith("_ACTION")]

# - Action Keys
ACTION_KEY = "action"
CSS_SELECTOR_KEY = "css_selector"
SUFFIX_KEY = "suffix"
FULL_NAME_KEY = "full_name"
CURRENT_URL_KEY = "current_url"
DURATION_KEY = "duration"
INPUT_KEY = "input"
INPUT_TYPE_KEY = "input_type"
VIEWPORT_ONLY_KEY = "viewport_only"
PATH_KEY = "path"
BYPASS_404_KEY = "bypass_404"
X_POSITION_KEY = "x_position"
Y_POSITION_KEY = "y_position"
POSITION_BOTTOM_KEY = "position_bottom"
POSITION_MIDDLE_KEY = "position_middle"
POSITION_TOP_KEY = "position_top"
SCROLL_PADDING_KEY = "scroll_padding"
PADDING_KEY = "padding"
SPECIAL_KEY_KEY = "key"
REFERENCE_KEY = "ref"
LIBRARY_KEY = "library"
ACTION_LIST_KEY = "actions"
ELEMENT_KEY = "element"
ALLOW_EMPTY = "allow_empty"
DO_NOT_INCREMENT_KEY = "do_not_increment_element_count"
CHILD_KEY = "child"
SCRIPT_KEY = "script"
INDEX_KEY = "index"
ADD_TO_MISC_KEY = "add_to_misc"
DEFAULT_CONTENT_KEY = "default_content"
WIDTH_KEY = "width"
HEIGHT_KEY = "height"
CONTENT_HEIGHT_KEY = "content_height"
PATHS_TO_SKIP_KEY = "paths_to_skip"
NAME_KEY = "name"
VALUE_KEY = "value"
CUSTOM_INPUT_KEY = "custom_input"
VISIBLE_KEY = "visible"

ALL_ACTION_KEYS = [local_[v] for v in dir() if v.endswith("_KEY")]

# Sitemap paths
AEM_NEW_SITEMAP_PATH = ".sitemap.xml" # For AEM 6.5 sites
DEFAULT_SITEMAP_PATH = "/sitemap.xml"

# AEM Login CSS Selectors
AEM_LOGIN_USERNAME_SELECTOR = "#username"
AEM_LOGIN_PASSWORD_SELECTOR = "#password"
AEM_LOGIN_SUBMIT_SELECTOR = "[type='submit']"

# ===================================================================
# --- Utility Variables
# ===================================================================
URL_REGEX = "^(?:http(s)?:\/\/)?[\w.:@-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
BEGINS_WITH_SLASH_REGEX = "(^$|^\/)"
WCM_MODE_DISABLED = "wcmmode=disabled"

URL_BLACKLIST = [".pdf", ".doc", "?mode=print"]

DEFAULT_MOBILE_BROWSER_SIZE = {WIDTH_KEY: 320, HEIGHT_KEY: 1000}
DEFAULT_DESKTOP_BROWSER_SIZE = {WIDTH_KEY: 1440, HEIGHT_KEY: 1000}

PASSED = "Passed"
FAILED = "Failed"

# ===================================================================
# --- Request Setup Helpers
# ===================================================================
def get_sitemap_path(project, config, base_url, content_path):
    # - Set up the sitemap path
    if config.get(PLATFORM):
        # AEM 6.5 uses the sitemap.xml resource in the DAM
        log.debug("AEM 6.5 detected")
        sitemap_path = f"{content_path}{AEM_NEW_SITEMAP_PATH}"

    else:
        # Use the sitemap path in the config if provided, else default to /sitemap.xml
        sitemap_path = config.get(SITEMAP_PATH, DEFAULT_SITEMAP_PATH)

    # - Add the path to the url under test's base url. We use domain for cases where the platform
    #   path is included in the test_url
    sitemap_url = f"{base_url}{sitemap_path}"
    return sitemap_url


def crawl(sitemap_url, browser_data, base_url, username, password, content_path=None):
    internal_urls = []
    sh = selenium_helpers.SeleniumHelpers()
    http = urllib3.PoolManager(cert_reqs = 'CERT_NONE')
    browser_under_test = browser_data.get(BROWSER_NAME)

    try:
        request = http.request("GET", sitemap_url)
        if check_if_author(sitemap_url) or request.status != 200:
            sh.create_driver(**browser_data)
            # sh.driver.set_page_load_timeout(30)
            sh.load_url(sitemap_url, bypass_status_code_check=True)
            time.sleep(5)
            if any(login_indicator in sh.get_current_url() for login_indicator in GENE_SAML_LOGIN_INDICATOR or AUTHOR_SITE_INDICATOR or DISPATCH_INDICATOR):
                log.debug("GENE SAML LOGIN DETECTED")
                platform_login(sh, base_url, username, password)
                sh.load_url(sitemap_url, bypass_status_code_check=True)
                time.sleep(5)

            soup = BeautifulSoup(sh.driver.page_source, "html.parser")
            discovered_urls = soup.find_all("loc")
        else:
            # Using the http response if it was successful.
            soup = BeautifulSoup(request.data, "html.parser")
            discovered_urls = soup.find_all("loc")

        for page in discovered_urls:
            page_link = page.text
            if all(blacklist not in page_link for blacklist in URL_BLACKLIST):
                # - Remove the path from the url to remove the prod domain from the path (if there)
                path = parse_url_path(page_link, content_path)

                # - Add it to the url list
                internal_urls.append(path)

        # Setting the browser back to what the user requested now that the crawl has completed.
        browser_data.update({BROWSER_NAME: browser_under_test})
    except Exception as e:
        if sh.driver:
            sh.quit_driver()
        log.warning(e)
        raise e

    finally:
        if sh.driver:
            sh.quit_driver()

    return internal_urls


def trim_sections(site_paths, content_path, site_sections=None, skip_sections=None):
    # - Remove any paths not in the site_sections
    # Gather "clean" paths from the list of site_paths
    urls_in_sections = []
    for path in site_paths:
        for section in site_sections:
            if path in urls_in_sections:
                continue

            if ("*" in section and all(
                    segment in path for segment in filter(None, section.split("*")))) or path.startswith(section):
                urls_in_sections.append(path)

    if urls_in_sections:
        site_paths = urls_in_sections
    elif site_sections:
        raise HippoThreadError("None of the site's urls started with one of the site_sections provided. "
                               "Please check the site sections you provided with the request to ensure they "
                               "were spelled correctly and submit it again")

    # - Remove any pages with a skip_section in the path
    approved_pages = []
    for path in site_paths:
        page_approved = True
        for section in skip_sections:
            if "*" in section and all(segment in path for segment in filter(None, section.split("*"))):
                page_approved = False
            elif path.startswith(section):
                page_approved = False

        if page_approved:
            approved_pages.append(path)

    if approved_pages:
        site_paths = approved_pages
    elif skip_sections:
        raise HippoThreadError("No pages remained after the skip_sections were removed from the list of urls")

    return site_paths


def add_urls_to_image_list(image_list, user, project, branch, base_url, site_paths, build_id, mobile,
                           browser_data, content_path):
    """Prepare the image_list that all of the image data will be added to"""
    # Make an entry in the image list for each page being captured
    for path in site_paths:
        if check_if_author(base_url):
            test_url = concatenate_test_url(base_url, path, content_path)
        else:
            test_url = base_url + path
        image_list["image_list"].append({"url": test_url, "path": path, "image_data": []})

    # Create a misc page object at the end
    image_list["image_list"].append({"url": MISC_PATH_TEXT, "path": MISC_PATH_TEXT, "image_data": []})

    return image_list


def parse_url_path(url, remove_from_path=None):
    # Replace removal string from url, if provided
    if remove_from_path:
        url = re.sub(remove_from_path, "", url)

    path = urlparse(url).path
    query = urlparse(url).query
    fragment = urlparse(url).fragment
    if fragment:
        path = f"{path}#{fragment}"
    if query:
        path = f"{path}?{query}"

    return path


def parse_domain(url):
    domain = urlparse(url).netloc
    return domain


def parse_base_url(url):
    parsed_uri = urlparse(url)
    base_url = f'{parsed_uri.scheme}://{parsed_uri.netloc}'
    return base_url


def check_if_author(url):
    if any(indicator in parse_domain(url) for indicator in AUTHOR_SITE_INDICATOR):
        return True
    return False

def check_if_dispatch(url):
    if any(indicator in parse_domain(url) for indicator in DISPATCH_INDICATOR):
        return True
    return False


def authenticate_browser(selenium_helper, url, username, password):
    auth_url = add_basic_auth(url, username, password)
    selenium_helper.load_url(auth_url, True)


def add_basic_auth(url, username, password):
    creds = f"{username}:{password}@"
    domain = urlparse(url).netloc
    auth_domain = creds + domain
    return url.replace(domain, auth_domain)


def remove_basic_auth(url):
    # Check whether the url is formatted to contain basic auth
    match = re.search('^(?P<protocol>.+?//)(?P<username>.+?):(?P<password>.+?)@(?P<address>.+)$', url)
    if match:
        # Build the
        auth = f"{match.group('username')}:{match.group('password')}@"
        return url.replace(auth, "")
    else:
        return url


def get_test_url(url, username=None, password=None):
    if username and password:
        url = add_basic_auth(url, username, password)
    # TODO: Discuss this verify=false thing with Josh. There should be a better solution to bad certs
    r = requests.get(url, verify=False)
    # Fail if the auth did not work
    if r.status_code == 401:
        # Remove the auth from the URL so that the creds are not printed out in the log
        remove_basic_auth(url)
        message = f"Received a bad status code when trying to access {url} : Status Code - {r.status_code}"
        raise HippoGeneralException(message)
    # - Return whichever url the request redirected to, if any (helps solve http vs https issues)
    # Re-add the basic auth to handle cases where the case of a redirect removes it
    if username and username not in r.url:
        return add_basic_auth(r.url, username, password)
    return r.url


def concatenate_test_url(url, path, content_path):
    # Create the default url string
    test_url = url + path

    # Add the content path to the url if testing in an author environment
    if check_if_author(test_url):
        # Break apart the url
        parsed_uri = urlparse(test_url)
        new_path = parsed_uri.path
        queries = parsed_uri.query
        fragments = parsed_uri.fragment

        # Check whether the content path already included in the path
        if content_path not in new_path:
            # Add it at the front of the path is it isn't
            new_path = content_path + new_path

        # Add wcmmode
        if queries:
            if WCM_MODE_DISABLED in queries:
                # Do not add wcmmode to the queries if it is already there
                new_path += f"?{queries}"
            else:
                # Append wcmmode to other queries if they are already included in the url
                new_path += f"?{queries}&{WCM_MODE_DISABLED}"
        else:
            new_path += f"?{WCM_MODE_DISABLED}"

        # Add fragments
        if fragments:
            new_path += f"#{fragments}"

        test_url = url + new_path

    return test_url


def platform_login(selenium_helper, url, username, password):
    log.info("Logging in to Platform")
    if not username or not password:
        raise HippoGeneralException("The AEM Username or Password were not provided. You cannot run "
                                    "screens in this AEM environment without providing the username "
                                    "and password when launching the Hippo service")
    selenium_helper.load_url(url, bypass_status_code_check=True)
    time.sleep(5)
    current_url = selenium_helper.get_current_url()
    try:
        if any(indicator in current_url for indicator in 
                GENE_SAML_LOGIN_INDICATOR or 
                AUTHOR_SITE_INDICATOR or 
                DISPATCH_INDICATOR) and selenium_helper.element_exists(AEM_LOGIN_USERNAME_SELECTOR):
            selenium_helper.wait_for_element(AEM_LOGIN_USERNAME_SELECTOR)
            selenium_helper.fill_an_element(username, AEM_LOGIN_USERNAME_SELECTOR)
            selenium_helper.fill_an_element(password, AEM_LOGIN_PASSWORD_SELECTOR)
            selenium_helper.click_an_element(AEM_LOGIN_SUBMIT_SELECTOR)
            log.info("Logged in successfully.")
        else:
            log.warning(current_url)
            log.warning("The current url was not recognized as an AEM login page when executing the "
                        "platform_login() method")

        time.sleep(5)
        if "login.error.html" in selenium_helper.get_current_url():
            message = "Unable to successfully log in."
            log.warning(message)
            raise HippoGeneralException(message)
    except Exception as e:
        log.error(f"An Error occurred when attempting to login to {current_url}: {e}")
        raise e


def create_html_log(image_list_data, result, start_date, start_time, error_list=None, site_sections=None,
                    skip_sections=None):
    screenshot_log_html = StringIO()

    # Format the site and skip section outputs
    includes = "<br>".join(site_sections) if site_sections else "All"
    excludes = "<br>".join(skip_sections) if skip_sections else "None"

    # - Write out file header with styling
    screenshot_log_html.write("<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 "
                              "Transitional//EN http://www.w3.org/TR/html4/loose.dtd'>\n")
    screenshot_log_html.write(
        """<html>\n<head>\n<meta http-equiv='Content-Type' content='text/html; charset=utf-8'>\n
        <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" \n>
        <style type=\"text/css\">
        <link
        <!--
        body{
            font-family: Helvetica;
            background-color:#fff;
            }
        a {
          color: #5197b1;
          text-decoration: none;
        }
        a:hover {
          color: #40788d;
          text-decoration: none;
        }
        #header{
        background-image: url("http://meltqa-hippo-prod.s3-us-west-1.amazonaws.com/screenshot_log/meltqa-bg.jpg");
        background-repeat:no-repeat;
        background-position:center;
        top-margin:0px;
        height:200px;
        }
        #header h1{
        font-size:80px;
        color:#fff;
        margin-top:0px;
        padding-top:40px;
        }
        table{
        margin-top:50px;
        }
        .bold{
            font-weight:bold;
        }
        .error{
            font-size:30px;
            background-color:#ff4d4d;
            border-radius:10px;
        }
        .error th{
            text-align:center;
            border-radius:5px;
            padding:10px;
            }
        .errorMessage{
            background-color:#F5F5F5;
        }
         </style>\n"""
    )
    # - Write out run data table heading
    # 0 = Project
    # 1 = Branch
    # 2 = Browser
    # 3 = Test Url
    # 4 = PDF Link
    screenshot_log_html.write("</head><body>")

    # TODO: Use constants for these keys
    screenshot_log_html.write(
        f"""
            <div id="header">
            <h1 style="text-align:center"> Hippo Log </h1>
            </div>
            <br>
        <div class="container">
        \n<table class="table table-striped">
        <tr><td><p class='bold'>Status</p><td><p>{result}</p></tr>
        <tr><td><p class='bold'>Project</p><td><p>{image_list_data["project"]}</p></tr>
        <tr><td><p class='bold'>Branch</p><td><p>{image_list_data["branch"]}</p></tr>
        <tr><td><p class='bold'>Browser</p><td><p>{image_list_data["driver_data"]["browserName"]}</p></tr>
        <tr><td><p class='bold'>Mobile</p><td><p>{image_list_data["mobile"]}</p></tr>
        <tr><td><p class='bold'>URL</p><td><p><a target=_blank href={image_list_data["test_url"]}>{image_list_data["test_url"]}</a></p></tr>
        <tr><td><p class='bold'>Included Areas</p><td><p>{includes}</p></tr>
        <tr><td><p class='bold'>Excluded Areas</p><td><p>{excludes}</p></tr>
        <tr><td><p class='bold'>Image_list</p><td><p><a target=_blank href={image_list_data["image_list_url"]}>{image_list_data["image_list_url"]}</a></p></tr>
        <tr><td><p class='bold'>PDF Link</p><td><p><a target=_blank href={image_list_data.get("pdf_url", "Not sent")}>{image_list_data.get("pdf_url", "Not sent")}</a></p></tr>
        <tr><td><p class='bold'>Start Time</p><td><p>{start_date}</p></tr>
        <tr><td><p class='bold'>Duration</p><td><p>{datetime.timedelta(seconds=time.time() - start_time)} (includes time in queue)</p></tr>
        </table><p><p>
        </div>
        """
    )

    # - Write out any errors caught during completion of the run
    if error_list:
        screenshot_log_html.write(
            """
            \n
            <div class="container errorHandler">
            <table>
            <thead class="table-rhino error">
            <th>Errors Found while running the screenshots</th>
            </thead>
            """
        )
        for error in error_list:
            screenshot_log_html.write(f"<tr><td><p class='errorMessage'>{error}</p></tr>")
        screenshot_log_html.write("</table></div>")

    # - Page Table headers
    screenshot_log_html.write(
        """
        <div class="container">
        \n<table class="table table-hover">
        <thead class=table-rhino>
        <th>PDF Page #</th><th>Image Name</th><th>Page URL</th>
        </thead>
        </div>
        """
    )

    # - Page/Image data
    page_number = 0

    # Check whwther there is misc data in the image list
    misc_data = {}
    misc = True if image_list_data["image_list"][-1]["url"] == MISC_PATH_TEXT else False
    if misc:
        # Remove and store the misc data
        misc_data = image_list_data["image_list"].pop(-1)

    for page in image_list_data["image_list"]:
        for image_num, image in enumerate(page["image_data"]):
            page_number += 1

            screenshot_log_html.write(
                f"""
                <tr>
                <td><p>{page_number}</p>
                <td><p><a target=_blank href={image["s3_location"]}>{image["filename"]}</a></p>
                <td><p><a target=_blank href={image["url"]}>{image["url"]}</a></p></tr>
                """)

    # Create a new block in the table if there is misc data
    if misc:
        screenshot_log_html.write(
            f"<th>{MISC_PATH_TEXT}</th>"
        )
        for image in misc_data["image_data"]:
            page_number += 1
            screenshot_log_html.write(
                f"""
                <tr>
                <td><p>{page_number}</p>
                <td><p><a target=_blank href={image["s3_location"]}>{image["filename"]}</a></p>
                <td><p><a target=_blank href={image["url"]}>{image["url"]}</a></p></tr>
                """
            )

    # - Close the file
    screenshot_log_html.write("</table>\n</body>\n</html>")
    screenshot_log_html.seek(0)

    return screenshot_log_html


# ===================================================================
# --- Basic Python Helpers
# ===================================================================
def read_json_from_path(path):
    """Reads from a file path and returns json
    :param
        -   path:   string path to read

    :returns
        Json data
    """
    if not os.path.exists(path):
        log.warn(f"Unable to read json from {path} because file doesn't exist!")
        return {}

    try:
        with open(path) as json_file:
            json_data = json.load(json_file)
        return json_data
    except ValueError as value_exception:
        log.error(f"Unable to read json from {path} because file doesn't "
                  f"contain correctly formatted json: {value_exception}")
        raise value_exception
    except Exception as e:
        log.error(f"Unexpected problem encountered while attempting to read json from {path}: {e}")
        raise e


def save_stringIO_file_locally(local_folder, filename, stringIO_file):
    ensure_directory_exists(local_folder)

    local_file = open(local_folder + filename, 'wb')
    stringIO_file.seek(0)
    shutil.copyfileobj(stringIO_file, local_file)
    local_file.close()


def get_screenshot_name(url_or_path):
    screenshot_name = parse_url_path(url_or_path)

    screenshot_name = screenshot_name.replace("/", "_")
    jsp_text = ".jsp"
    html_text = ".html"
    pdf_text = ".pdf"
    htm_text = ".htm"
    wcm_mode = "\?wcmmode=disabled"
    remove_strings = [jsp_text, html_text, htm_text, wcm_mode, pdf_text, pdf_text.upper()]
    replace_strings = ["#", "\?", "&"]

    for string in remove_strings:
        screenshot_name = re.sub(string, "", screenshot_name)

    for string in replace_strings:
        screenshot_name = re.sub(string, "_", screenshot_name)

    if screenshot_name == "" or screenshot_name == "_":
        screenshot_name = "home_page"
    else:
        if screenshot_name[0] == "_":
            screenshot_name = screenshot_name[1:]

    return screenshot_name


def ensure_directory_exists(directory):
    d = os.path.dirname(directory)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def create_logger(log_name):
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s at line %(lineno)d - %(message)s (%(threadName)s)",
        datefmt="%Y-%m-%d %I:%M:%S %p",
        level="INFO")

    new_logger = logging.getLogger(log_name)

    return new_logger


def send_job_to_rhino(project, url, branch, user, build_id, screenshot_log_path, result, rhino_host, job_link):
    rhino_client = RhinoClient(
        test_name=RHINO_TEST_NAME, url=url, brand=project, branch=branch,
        user=user, rhino_client_url=rhino_host, build_id=build_id)

    rhino_client.set_log(file_path=screenshot_log_path, link_text="log")
    rhino_client.send_test(result)
    log.info(f"Rhino Link: {job_link}")


def send_emails(mandrill_key, project, url, branch, screenshot_log_path, result, recipients, job_link=None):
    email = EmailClient(mandrill_key)
    subject = f"Screenshots for {project}'s {branch} branch: {result.upper()}"
    failed_icon = "http://qa-screenshots.s3.amazonaws.com/icons/icon-build-failed.png"
    warning_icon = "http://qa-screenshots.s3.amazonaws.com/icons/icon-build-warning.png"
    passing_icon = "http://qa-screenshots.s3.amazonaws.com/icons/icon-build-successful.png"
    branch_icon = "http://qa-screenshots.s3.amazonaws.com/icons/branch.png"

    if result == PASSED:
        result_html = f"<img src={passing_icon}> {result}"
    else:
        result_html = f"<img src={failed_icon}> {result}"

    if job_link:
        message = f"""
        <p>Your screenshot job for {project} on the <img src={branch_icon}>{branch} - {result_html}</p>
        <p>You can find the screenshot log file here: <a href={screenshot_log_path}><b>LOG</b></a></p>
        <p>You can find the Rhino Job here: <a href={job_link}><b>RHINO</b></a></p><br>
        """
        email.send_email("jaswant.singh@growthnatives.com", recipients, message, subject, "Hippo")
    else:
        message = f"""
        <p>Your screenshot job for {project} on the <img src={branch_icon}>{branch} - {result_html}</p>
        <p>You can find the screenshot log file here: <a href={screenshot_log_path}><b>LOG</b></a></p>
        """
        email.send_email("jaswant.singh@growthnatives.com", recipients, message, subject, "Hippo")


def close_iperceptions(selenium_helper):
    if "www." in selenium_helper.get_current_url():
        try:
            log.debug("Waiting for the iPerceptions popup....")
            selenium_helper.wait_for_element("[name=IPEMap] [alt='no']", 10, visible=True)
            selenium_helper.execute_script("""document.querySelector("[name=IPEMap] [alt='no']").click()""")
            time.sleep(2)
        except selenium_helpers.TimeoutError:
            log.debug("No iPerceptions popup found on this production site. Moving on without closing it")


def close_gene_cookie_modal(selenium_helper):
    try:
        log.debug("Waiting for the Cookie Modal....")
        selenium_helper.wait_for_element("body #onetrust-accept-btn-handler", 5, visible=True)
        selenium_helper.click_an_element("body #onetrust-accept-btn-handler")
        time.sleep(2)
    except selenium_helpers.TimeoutError:
        log.debug("No cookie modal found. Moving on without closing it.")


def get_all_github_branches(github_token, hippo_sites_repo):
    """
    This will use the GitHub API to get a list of branches in a specified GitHub repository.
    :param
        - github_token: string - This token will be used to connect to the GitHub API.
        - hippo_sites_repo: string - Path of the repository used to pull in configurations. E.g. 'username/meltmedia'
    :return
        - branches: list - A list of current branches in the hippo_sites_repo sent in.
    """
    github = Github(github_token)
    repo = github.get_repo(hippo_sites_repo)
    branches = []
    for branch in repo.get_branches():
        branches.append(branch.name)
    return branches


def get_config_list(repo, branch, directory, headers, local_path=None):
    config_files = []
    if local_path:
        local_sites_path = os.path.join(local_path, directory)
        found_files = [f for f in os.listdir(local_sites_path)
                       if os.path.isfile(os.path.join(local_sites_path, f))]
        for file_name in found_files:
            if file_name.endswith(".json"):
                config_files.append(file_name)
    else:
        # sites_path = "/repos/meltmedia/{}/contents/{}?ref={}".format(repo, directory, branch)
        sites_path = f"repos/{repo}/meltmedia/contents/hippo-sites/{directory}?ref={branch}"
        resp = requests.get(f"https://api.github.com/{sites_path}", headers=headers)

        logging.info(f"API URL Response from Github {resp.status_code}")

        config_list = json.loads(resp.content)
        for config in config_list:
            config_files.append(config["name"])

    logger.info(f"Config file {config_files}")
    return config_files


def get_configuration_from_github(project, github_branch, environment, github_token, github_repo):
    config_filename = f"{project}.json"
    project_config = None

    headers = {"Authorization": f"token {github_token}"}

    # Get a list of all configs available for Hippo (on this environment's branch)
    try:
        config_list = get_config_list(github_repo, github_branch, "sites", headers)
        logger.info(f"Config lists {config_list}")
    except Exception as e:
        print("Unable to fetch config list ", e)

    # - Check whether a config file exists for theis project and branch combination
    if config_filename in config_list:
        pass
    else:
        # A config for this project does not exist. Throw an error and freak out!
        message = f"There does not appear to be a Hippo config on Github for the project {project!r}. " \
                  "Please speak with your QA representative to troubleshoot the issue."
        log.error(message)
        raise HippoGeneralException(message)

    # - Request the config data
    repo_path = f"{github_repo}/meltmedia/{github_branch}/hippo-sites/sites/{config_filename}"
    resp = requests.get(f"https://raw.githubusercontent.com/{repo_path}", headers=headers)
    # Check that the respone had a good status code
    if resp.status_code > 400:
        message = f"A bad status code of {resp.status_code} was returned when attempting to grab the config file at {repo_path}. " \
                  f"Please see your QA rep for help troubleshooting this issue: {resp.text}"
        log.error(message)
        raise HippoGeneralException(message)

    # Load the response data into a json object
    project_config = json.loads(resp.content)

    return project_config


def get_active_sauce_tunnel(sauce_labs_username, sauce_labs_access_key):
    """
    This will check to see if there are any Sauce Labs tunnels up and running. If there are it will loop through each
    of the tunnels and get the number of jobs running on the tunnel and the name of the tunnel. If the number of jobs
    running on the tunnel is less than 2 it will update the browser to use that tunnel.
    :param
        - sauce_labs_username: String - The specific username used to authorize with Sauce Labs
        - sauce_labs_access_key: String - The specific Access Key tied to the username used to authorize with Sauce Labs
    """
    tunnel_identifier = ""
    try:
        running_tunnels = requests.get(
            f"https://{sauce_labs_username}:{sauce_labs_access_key}@saucelabs.com/rest/v1/{sauce_labs_username}/tunnels"
        )
        if running_tunnels.status_code != 200:
            return False
        elif len(running_tunnels.json()) == 0:
            return False

        for running_tunnel in running_tunnels.json():
            number_of_running_jobs = requests.get(
                f"https://{sauce_labs_username}:{sauce_labs_access_key}@saucelabs.com/rest/v1/{sauce_labs_username}/tunnels/{running_tunnel}/num_jobs".json())
            tunnel = requests.get(f"https://{sauce_labs_username}:{sauce_labs_access_key}@saucelabs.com/rest/v1/{sauce_labs_username}/tunnels/{running_tunnel}".json())
            if number_of_running_jobs["jobs_running"] < 2 and tunnel["shared_tunnel"]:
                tunnel_identifier = tunnel["tunnel_identifier"]
                return tunnel_identifier

        return False

    except Exception as request_exception:
        message = f"Sauce Labs may be unavailable at this time: {request_exception}"
        log.error(message)
        return False


# ===================================================================
# --- Exception Classes
# ===================================================================
class HippoGeneralException(Exception):
    def __init__(self, msg, stacktrace=None, details=None):
        self.msg = msg
        self.details = details or {}
        self.stacktrace = stacktrace
        super(HippoGeneralException, self).__init__()

    def __str__(self):
        exception_msg = "{}".format(self.msg)
        if self.details:
            detail_string = "\nDetails:\n"
            for key, value in self.details.items():
                detail_string += "{}: {}\n".format(key, value)
            exception_msg += detail_string
        if self.stacktrace is not None:
            exception_msg += "{}".format(self.stacktrace)

        return exception_msg


class MissingKey(HippoGeneralException):
    def __init__(self, message, key, stacktrace=None, details=None):
        super(MissingKey, self).__init__(msg=message, stacktrace=stacktrace, details=details)
        self.key = "{0}".format(key)
        if details:
            self.details["missing_key"] = details.get("missing_key") or key


class HippoThreadError(HippoGeneralException):
    def __init__(self, message, stacktrace=None, details=None):
        details = details or {}
        super(HippoThreadError, self).__init__(msg=message,
                                               stacktrace=stacktrace,
                                               details=details)