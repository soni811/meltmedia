from action_constants import *
from the_ark.input_generator import STRING_FIELD, EMAIL_FIELD, PHONE_FIELD, ZIP_CODE_FIELD, DATE_FIELD, PASSWORD_FIELD


ACTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "array",
    "items": {
        "oneOf": [
            {
                "properties": {
                    ACTION_KEY: {"enum": [LOAD_URL_ACTION]},
                    PATH_KEY: {"type": "string"},
                    URL_KEY: {"type": "string"},
                    BYPASS_404_KEY: {"type": "boolean"}
                },
                "additionalProperties": False,
                "anyOf": [
                    {"required": [PATH_KEY]},
                    {"required": [URL_KEY]}
                ]
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [CLICK_ACTION, HOVER_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "additionalProperties": False,
                "required": [CSS_SELECTOR_KEY]
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [CLICK_ELEMENT_WITH_OFFSET_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    X_POSITION_KEY: {"type": "integer"},
                    Y_POSITION_KEY: {"type": "integer"},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "additionalProperties": False,
                "required": [CSS_SELECTOR_KEY]
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [ENTER_TEXT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    INPUT_KEY: {"type": "string"},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "required": [CSS_SELECTOR_KEY, INPUT_KEY],
                "additionalProperties": False,
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [ENTER_TEXT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    INPUT_TYPE_KEY: {"enum": [STRING_FIELD, EMAIL_FIELD, PHONE_FIELD,
                                              ZIP_CODE_FIELD, DATE_FIELD, PASSWORD_FIELD]},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "required": [CSS_SELECTOR_KEY, INPUT_TYPE_KEY],
                "additionalProperties": False,
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SCROLL_WINDOW_TO_POSITION_ACTION]},
                    X_POSITION_KEY: {"type": "integer"},
                    Y_POSITION_KEY: {"type": "integer"},
                    POSITION_TOP_KEY: {"type": "boolean"},
                    POSITION_BOTTOM_KEY: {"type": "boolean"},
                },
                "additionalProperties": False,
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SCROLL_WINDOW_TO_ELEMENT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    POSITION_BOTTOM_KEY: {"type": "boolean"},
                    POSITION_MIDDLE_KEY: {"type": "boolean"},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "required": [CSS_SELECTOR_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SCROLL_AN_ELEMENT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    X_POSITION_KEY: {"type": "integer"},
                    Y_POSITION_KEY: {"type": "integer"},
                    POSITION_TOP_KEY: {"type": "boolean"},
                    POSITION_BOTTOM_KEY: {"type": "boolean"},
                    SCROLL_PADDING_KEY: {"type": "integer"},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "additionalProperties": False,
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [REFRESH_ACTION]}
                },
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SLEEP_ACTION]},
                    DURATION_KEY: {"type": "number"}
                },
                "required": [DURATION_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [WAIT_FOR_ELEMENT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    DURATION_KEY: {"type": "number"}
                },
                "required": [CSS_SELECTOR_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SEND_SPECIAL_KEY_ACTION]},
                    SPECIAL_KEY_KEY: {"type": "string"}
                },
                "required": [SPECIAL_KEY_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [FOR_EACH_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"},
                    ACTION_LIST_KEY: {
                        "type": "array",
                        # TODO: Could not get the reference to ensure actions are in the list to work!
                        # "items": {
                        #     "$ref": "#/definitions/action_data"
                        # }
                    },
                    CHILD_KEY: {"type": "boolean"},
                    DO_NOT_INCREMENT_KEY: {"type": "boolean"},
                    ALLOW_EMPTY_KEY: {"type": "boolean"}
                },
                "required": [CSS_SELECTOR_KEY, ACTION_LIST_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SHOW_ELEMENT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"}
                },
                "required": [CSS_SELECTOR_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [HIDE_ELEMENT_ACTION]},
                    CSS_SELECTOR_KEY: {"type": "string"}
                },
                "required": [CSS_SELECTOR_KEY],
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [SWITCH_WINDOW_HANDLE_ACTION]},
                    INDEX_KEY: {"type": "integer"}
                },
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [CLOSE_WINDOW_ACTION]}
                },
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [FOCUS_ACTION]}
                },
                "additionalProperties": False
            },
            {
                "properties": {
                    ACTION_KEY: {"enum": [EXECUTE_SCRIPT_ACTION]},
                    SCRIPT_KEY: {"type": "string"},
                    ELEMENT_KEY: {"type": "boolean"}
                },
                "required": [SCRIPT_KEY],
                "additionalProperties": False
            }
        ]
    }
}

