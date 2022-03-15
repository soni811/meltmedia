from hippo.util import *
from src.the_ark.field_handlers import *

ID = "id"
LABEL = "label"
FIELDS = "fields"
DESCRIPTION = "description"
TYPE = "type"
DEFAULT = "default"
REQUIRED = "required"
OPTIONS = "options"
GROUP = "group"

# Field Types
TEXT = "text"
SELECT = "select"
CHECKBOX = "checkbox"
INTEGER = "integer"
DATE = "date"

actions = [
    {
        ID: CAPTURE_ACTION,
        LABEL: "Capture",
        DESCRIPTION: "Takes a screenshot of the page in its current state",
        FIELDS: [
            {
                ID: SUFFIX_KEY,
                LABEL: "Suffix",
                DESCRIPTION: "The identifier you'd like to give this image. It will be appended to the end of this page's path to generate the name of the image.",
                TYPE: TEXT,
                DEFAULT: None,
                REQUIRED: True,
                GROUP: "filename"
            },
            {
                ID: VIEWPORT_ONLY_KEY,
                LABEL: "Capture only visible area?",
                DESCRIPTION: "The identifier you'd like to give this image. It will be appended to the end of this page's path.",
                TYPE: CHECKBOX,
                DEFAULT: False,
                REQUIRED: False
            },
            {
                ID: SCROLL_PADDING_KEY,
                LABEL: "Pixel Overlap",
                DESCRIPTION: "Used when taking Paginated screenshots. Sets the amount of pixels that display on both images. Helps ensure that no content is cut off. This will overwrite the default Overlap for this capture",
                TYPE: CHECKBOX,
                DEFAULT: None,
                REQUIRED: False
            },
            {
                ID: FULL_NAME_KEY,
                LABEL: "Full Image Name",
                DESCRIPTION: """WARNING: Using this option overwrites the default image naming convention.\n
                             This will be used as the full image name. Be careful not to use the same name twice or the second will save over this image""",
                TYPE: CHECKBOX,
                DEFAULT: None,
                REQUIRED: True,
                GROUP: "filename"
            },
        ]
    },
    {
        ID: CLICK_ACTION,
        LABEL: "Click",
        DESCRIPTION: "Scroll to and Click an element on the page",
        FIELDS: [
            {
                ID: CSS_SELECTOR_KEY,
                LABEL: "CSS Selector",
                DESCRIPTION: "The CSS Selector that specifies the element you'd like to click.",
                TYPE: TEXT,
                DEFAULT: "",
                REQUIRED: True
            }
        ]
    },
    {
        ID: ENTER_TEXT_ACTION,
        LABEL: "Enter Text",
        DESCRIPTION: "Type text into an input field on the page",
        FIELDS: [
            {
                ID: CSS_SELECTOR_KEY,
                LABEL: "CSS Selector",
                DESCRIPTION: "The CSS Selector that specifies the element you'd like to enter text into.",
                TYPE: TEXT,
                DEFAULT: "",
                REQUIRED: True
            },
            {
                ID: INPUT_KEY,
                LABEL: "Input",
                DESCRIPTION: "The text you would like to type into the input field",
                TYPE: TEXT,
                DEFAULT: "",
                GROUP: "text_input",
                REQUIRED: True
            },
            {
                ID: INPUT_TYPE_KEY,
                LABEL: "Input Type",
                DESCRIPTION: """WARNING: Using this option overrides anything you types into the 'Input' field\n
                                The selected type of input will be randomly generated and used as the input text.""",
                TYPE: SELECT,
                DEFAULT: "",
                OPTIONS: [
                    {LABEL: "String", ID: STRING_FIELD},
                    {LABEL: "Email", ID: EMAIL_FIELD},
                    {LABEL: "Phone Number", ID: PHONE_FIELD},
                    {LABEL: "Zip Code", ID: ZIP_CODE_FIELD},
                    {LABEL: "Date", ID: DATE_FIELD}
                ],
                GROUP: "text_input",
                REQUIRED: True
            },
        ]
    },
]
