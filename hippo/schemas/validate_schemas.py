import jsonschema
from jsonschema.exceptions import ValidationError, RefResolutionError
from hippo.schemas.config_schema import CONFIG_SCHEMA
from hippo.schemas.request_schema import REQUEST_SCHEMA


class SchemaValidationException(Exception):
    def __init__(self, message=None, schema_data=None, schema=None, stacktrace=""):
        self.message = message
        self.data = schema_data if schema_data is not None else {}
        self.schema = schema if schema is not None else {}
        self.details = schema_data if schema_data is not None else {}

        self.code = 'SCHEMA_VALIDATION_ERROR'
        self.details["stacktrace"] = stacktrace

    def __str__(self):
        # TODO: Make this better
        return self.message

    def to_dict(self):
        self.details['data'] = self.data
        self.details['schema'] = self.schema
        return {
            'message': self.message,
            'code': self.code,
            'details': self.details
        }


class ConfigValidationError(SchemaValidationException):

    def __init__(self, message, config_data=None, schema=None):
        super(ConfigValidationError, self).__init__(message, config_data, schema)
        self.code = 'CONFIG_VALIDATION_ERROR'


class RequestValidationError(SchemaValidationException):

    def __init__(self, message, request_data=None, schema=None):
        super(RequestValidationError, self).__init__(message, request_data, schema)
        self.code = 'REQUEST_VALIDATION_ERROR'


def _validate(data, schema):
    """Validates json against a schema
    :param
        -   request:    JSON Dict to validate
        -   schema:     Schema to validate against

    :returns
        True if valid data
    """
    try:
        jsonschema.validate(data, schema)
    except (ValidationError, RefResolutionError) as jsonschema_exception:
        # TODO: Check for specific errors, like URL's that have a slash at the end, and give specific messages back
        message = f"The given data was not valid based on the given schema: {jsonschema_exception}"
        raise SchemaValidationException(message, data, schema)
    except Exception as e:
        error_message = f"Unexpected problem encountered while validating the data against the schema. " \
                        "Caught Exception: {e}"
        raise SchemaValidationException(error_message, data, schema)

    return True


def validate_project_config(project_config):
    """Validates a project config against the schema
    :param
        -   project_config: Dict containing a project config

    :returns
        True if valid config
    """
    result = _validate(project_config, CONFIG_SCHEMA)

    return result


def validate_hippo_request(request, schema=REQUEST_SCHEMA):
    """Validates an emu request against a request schema
    :param
        -   request:    Request dict
        -   schema:     Request schema. DEFAULT: etc.request_schemas.TEST_FORMS

    :returns
        True if valid request
    """
    #TODO: Catch exception and pass it up
    result = _validate(request, schema)

    return result