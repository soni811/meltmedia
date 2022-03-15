import hippo.util as c
from src.the_ark.field_handlers import STRING_FIELD, EMAIL_FIELD, PHONE_FIELD, ZIP_CODE_FIELD, DATE_FIELD

CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        c.PROJECT: {"type": "string"},
        c.SITEMAP_PATH: {
            "type": "string",
            "pattern": c.BEGINS_WITH_SLASH_REGEX
        },
        c.PLATFORM: {"type": "boolean"},
        c.PFIZER: {"type": "boolean"},
        c.THREAD_COUNT: {"type": "integer"},
        c.HIDDEN_PAGES: {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": c.BEGINS_WITH_SLASH_REGEX
            }
        },
        c.SECURE_PAGES: {
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
        c.SKIP_SECTIONS: {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        c.CONTENT_PATH: {
            "type": "string",
            "pattern": c.BEGINS_WITH_SLASH_REGEX
        },
        c.CUSTOM_INPUTS: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    c.LABEL: {"type": "string"},
                    c.DESCRIPTION: {"type": "string"}
                },
                "required": [c.LABEL],
                "additionalProperties": False,
            },
        },
        c.RESIZE_DELAY: {"type": "number"},
        c.ENVIRONMENTS: {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                c.DESKTOP_ENVIRONMENT: {
                    "$ref": "#/definitions/environment_data"
                },
                c.MOBILE_ENVIRONMENT: {
                    "$ref": "#/definitions/environment_data"
                },
                c.COMMON_ENVIRONMENT: {
                    "$ref": "#/definitions/environment_data"
                },
                c.REFERENCE_ENVIRONMENT: {
                    "type": "object",
                    "properties": {
                        c.PAGES: {
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/page_data"
                            }
                        },
                    },
                    "additional_properties": False
                }
            }
        }
    },
    "definitions": {
        "page_data": {
            "type": "object",
            "properties": {
                "path": {
                    "oneOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    ]
                },
                c.ACTION_LIST_KEY: {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/action_data"
                    }
                }
            },
            "required": [c.PATH_KEY, c.ACTION_LIST_KEY],
            "minItems": 1
        },
        "action_data": {
            "type": "object",
            "properties": {
                c.ACTION_KEY: {
                    "type": "string",
                    "enum": c.All_ACTION_TYPES
                },
            },
            "required": [c.ACTION_KEY],
            "oneOf": [
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CAPTURE_ACTION]},
                        c.SUFFIX_KEY: {"type": "string"},
                        c.SCROLL_PADDING_KEY: {"type": "integer"},
                        c.FULL_NAME_KEY: {"type": "string"},
                        c.CURRENT_URL_KEY: {"type": "boolean"},
                        c.VIEWPORT_ONLY_KEY: {"type": "boolean"},
                        c.ADD_TO_MISC_KEY: {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CAPTURE_SCROLLING_ELEMENT_ACTION]},
                        c.SUFFIX_KEY: {"type": "string"},
                        c.FULL_NAME_KEY: {"type": "string"},
                        c.CURRENT_URL_KEY: {"type": "boolean"},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.VIEWPORT_ONLY_KEY: {"type": "boolean"},
                        c.ADD_TO_MISC_KEY: {"type": "boolean"},
                        c.SCROLL_PADDING_KEY: {"type": "integer"}
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.SUFFIX_KEY],
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CAPTURE_SCROLLING_ELEMENT_ACTION]},
                        c.SUFFIX_KEY: {"type": "string"},
                        c.FULL_NAME_KEY: {"type": "string"},
                        c.CURRENT_URL_KEY: {"type": "boolean"},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.VIEWPORT_ONLY_KEY: {"type": "boolean"},
                        c.ADD_TO_MISC_KEY: {"type": "boolean"},
                        c.SCROLL_PADDING_KEY: {"type": "integer"}
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.FULL_NAME_KEY],
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CAPTURE_ELEMENT_ACTION]},
                        c.SUFFIX_KEY: {"type": "string"},
                        c.FULL_NAME_KEY: {"type": "string"},
                        c.CURRENT_URL_KEY: {"type": "boolean"},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.ADD_TO_MISC_KEY: {"type": "boolean"},
                        c.PADDING_KEY: {"type": "integer"},
                        c.ELEMENT_KEY: {"type": "boolean"},
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.SUFFIX_KEY],
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.LOAD_URL_ACTION]},
                        c.PATH_KEY: {"type": "string"},
                        c.BYPASS_404_KEY: {"type": "boolean"}
                    },
                    "additionalProperties": False,
                    "required": [c.PATH_KEY]
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CLICK_ACTION, c.HOVER_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "additionalProperties": False,
                    "required": [c.CSS_SELECTOR_KEY]
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CLICK_ELEMENT_WITH_OFFSET_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.X_POSITION_KEY: {"type": "integer"},
                        c.Y_POSITION_KEY: {"type": "integer"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "additionalProperties": False,
                    "required": [c.CSS_SELECTOR_KEY]
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.ENTER_TEXT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.INPUT_KEY: {"type": "string"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.INPUT_KEY],
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.ENTER_TEXT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.INPUT_TYPE_KEY: {"enum": [STRING_FIELD, EMAIL_FIELD, PHONE_FIELD,
                                                    ZIP_CODE_FIELD, DATE_FIELD]},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.INPUT_TYPE_KEY],
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.ENTER_TEXT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.CUSTOM_INPUT_KEY: {"type": "string"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.CUSTOM_INPUT_KEY],
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SCROLL_WINDOW_TO_POSITION_ACTION]},
                        c.X_POSITION_KEY: {"type": "integer"},
                        c.Y_POSITION_KEY: {"type": "integer"},
                        c.POSITION_TOP_KEY: {"type": "boolean"},
                        c.POSITION_BOTTOM_KEY: {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SCROLL_WINDOW_TO_ELEMENT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.POSITION_BOTTOM_KEY: {"type": "boolean"},
                        c.POSITION_MIDDLE_KEY: {"type": "boolean"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "required": [c.CSS_SELECTOR_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SCROLL_AN_ELEMENT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.X_POSITION_KEY: {"type": "integer"},
                        c.Y_POSITION_KEY: {"type": "integer"},
                        c.POSITION_TOP_KEY: {"type": "boolean"},
                        c.POSITION_BOTTOM_KEY: {"type": "boolean"},
                        c.SCROLL_PADDING_KEY: {"type": "integer"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "additionalProperties": False,
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.REFRESH_ACTION]}
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SLEEP_ACTION]},
                        c.DURATION_KEY: {"type": "number"}
                    },
                    "required": [c.DURATION_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.WAIT_FOR_ELEMENT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.DURATION_KEY: {"type": "number"},
                        c.VISIBLE_KEY: {"type": "boolean"}
                    },
                    "required": [c.CSS_SELECTOR_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SEND_SPECIAL_KEY_ACTION]},
                        c.SPECIAL_KEY_KEY: {"type": "string"}
                    },
                    "required": [c.SPECIAL_KEY_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.REFERENCE_ACTION]},
                        c.REFERENCE_KEY: {"type": "string"}
                    },
                    "required": [c.REFERENCE_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.REFERENCE_ACTION]},
                        c.REFERENCE_KEY: {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [c.REFERENCE_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.FOR_EACH_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.ACTION_LIST_KEY: {
                            "type": "array",
                            # TODO: Could not get the reference to ensure actions are in the list to work!
                            # "items": {
                            #     "$ref": "#/definitions/action_data"
                            # }
                        },
                        c.CHILD_KEY: {"type": "boolean"},
                        c.DO_NOT_INCREMENT_KEY: {"type": "boolean"},
                        c.ALLOW_EMPTY: {"type": "boolean"}
                    },
                    "required": [c.CSS_SELECTOR_KEY, c.ACTION_LIST_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SHOW_ELEMENT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"}
                    },
                    "required": [c.CSS_SELECTOR_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.HIDE_ELEMENT_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"}
                    },
                    "required": [c.CSS_SELECTOR_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SWITCH_WINDOW_HANDLE_ACTION]},
                        c.INDEX_KEY: {"type": "integer"}
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.SWITCH_WINDOW_IFRAME_ACTION]},
                        c.CSS_SELECTOR_KEY: {"type": "string"},
                        c.DEFAULT_CONTENT_KEY: {"type": "boolean"},
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.ADD_COOKIE_ACTION]},
                        c.NAME_KEY: {"type": "string"},
                        c.VALUE_KEY: {"type": "string"}
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.DELETE_COOKIE_ACTION]},
                        c.NAME_KEY: {"type": "string"}
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.CLOSE_WINDOW]}
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": ["focus"]}
                    },
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.EXTERNAL_REFERENCE_ACTION]},
                        c.LIBRARY_KEY: {"type": "string"},
                        c.REFERENCE_KEY: {
                            "oneOf": [
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "array"
                                }
                            ]
                        }
                    },
                    "required": [c.LIBRARY_KEY, c.REFERENCE_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.EXECUTE_SCRIPT_ACTION]},
                        c.SCRIPT_KEY: {"type": "string"},
                        c.ELEMENT_KEY: {"type": "boolean"}
                    },
                    "required": [c.SCRIPT_KEY],
                    "additionalProperties": False
                },
                {
                    "properties": {
                        c.ACTION_KEY: {"enum": [c.RESIZE_BROWSER_ACTION]},
                        c.WIDTH_KEY: {"type": "integer"},
                        c.HEIGHT_KEY: {"type": "integer"},
                        c.CONTENT_HEIGHT_KEY: {"type": "boolean"},
                        c.CSS_SELECTOR_KEY: {"type": "string"}
                    },
                    "additionalProperties": False
                }
            ]
        },
        "environment_data": {
            "type": "object",
            "properties": {
                c.PAGES: {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/page_data"
                    }
                },
                c.PAGINATED: {"type": "boolean"},
                c.FOOTERS: {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                c.HEADERS: {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                c.BROWSER_SIZE: {
                    "type": "object",
                    "properties": {
                        c.WIDTH_KEY: {"type": "integer"},
                        c.HEIGHT_KEY: {
                            "type": "integer",
                            "maximum": 8192
                        }
                    }
                },
                c.BEFORE_SCREENSHOT_KEY: {
                    c.ACTION_LIST_KEY: {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/action_data"
                        }
                    },
                    c.PATHS_TO_SKIP_KEY: {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "required": [c.ACTION_LIST_KEY]
                },
                c.CONTENT_CONTAINER_SELECTOR_KEY: {"type": "string"},
                c.SCROLL_PADDING_KEY: {"type": "integer"}
            },
            "additionalProperties": False,
        }
    }
}
