import hippo.util as c
from src.the_ark.email_client import EMAIL_REGEX
REQUEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        c.PROJECT: {"type": "string"},
        c.URL: {"type": "string",
                "pattern": c.URL_REGEX},
        c.BRANCH: {"type": "string"},
        c.SEND_TO_RHINO: {"type": "boolean"},
        c.CONTENT_PATH: {"type": "string",
                         "pattern": c.BEGINS_WITH_SLASH_REGEX},
        c.BROWSER: {
            "type": "object",
            "properties": {
                c.BROWSER_NAME: {"type": "string"},
                "mobile": {"type": "boolean"},
                "access_key": {"type": "string"},
                "username": {"type": "string"},
                c.HEADLESS: {"type": "boolean"},
                c.WEBDRIVER: {"type": "string"},
                c.BINARY: {"type": "string"},
                c.SCALE_FACTOR: {"type": "integer"},
                c.USE_SAUCE_LABS: {"type": "boolean"}
            },
            "required": [c.BROWSER_NAME]
        },
        c.USER: {"type": "string"},
        c.BUILD_ID: {"type": "string"},
        c.THREAD_COUNT: {"type": "integer"},
        c.MOBILE_ENVIRONMENT: {"type": "boolean"},
        c.LOCAL_CONFIG_PATH: {"type": "string"},
        c.GITHUB_DIRECTORY.lower(): {"type": "string"},
        c.PAGINATED: {"type": "boolean"},
        c.FILE_EXTENSION_PARAMETER: {
            "enum": [c.PNG_FILE_EXTENSION, c.JPEG_FILE_EXTENSION, c.BMP_FILE_EXTENSION]
        },
        c.CROP_IMAGES_FOR_PDF: {"type": "boolean"},
        c.SKIP_SECTIONS: {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        c.START_DATE: {
            "type": "string"
        },
        c.START_TIME: {
            "type": "number"
        },
        c.SITE_SECTIONS: {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        c.SITE_PATHS: {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": c.BEGINS_WITH_SLASH_REGEX
            }
        },
        c.RECIPIENTS: {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": EMAIL_REGEX
            }
        },
        c.CUSTOM_INPUTS: {"type": "object"},
        c.BROWSER_SIZE: {
            "type": "object",
            "properties": {
                c.WIDTH_KEY: {"type": "integer"},
                c.HEIGHT_KEY: {"type": "integer"}
            },
            "additionalProperties": False
        }
    },
    "required": [c.PROJECT, c.URL, c.USER],   "additionalProperties": False
}