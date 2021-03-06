from functools import wraps
from inspect import iscoroutinefunction

import falcon

try:
    import jsonschema
except ImportError:  # pragma: nocover
    pass


def validate(req_schema=None, resp_schema=None):
    """Decorator for validating ``req.media`` using JSON Schema.

    This decorator provides standard JSON Schema validation via the
    ``jsonschema`` package available from PyPI. Semantic validation via
    the *format* keyword is enabled for the default checkers implemented
    by ``jsonschema.FormatChecker``.

    Note:
        The `jsonschema`` package must be installed separately in order to use
        this decorator, as Falcon does not install it by default.

        See `json-schema.org <http://json-schema.org/>`_ for more
        information on defining a compatible dictionary.

    Args:
        req_schema (dict, optional): A dictionary that follows the JSON
            Schema specification. The request will be validated against this
            schema.
        resp_schema (dict, optional): A dictionary that follows the JSON
            Schema specification. The response will be validated against this
            schema.

    Example:
        .. code:: python

            from falcon.media.validators import jsonschema

            # -- snip --

            @jsonschema.validate(my_post_schema)
            def on_post(self, req, resp):

            # -- snip --

    """

    def decorator(func):
        if iscoroutinefunction(func):
            return _validate_async(func, req_schema, resp_schema)

        return _validate(func, req_schema, resp_schema)

    return decorator


def _validate(func, req_schema=None, resp_schema=None):
    @wraps(func)
    def wrapper(self, req, resp, *args, **kwargs):
        if req_schema is not None:
            try:
                jsonschema.validate(
                    req.media, req_schema,
                    format_checker=jsonschema.FormatChecker()
                )
            except jsonschema.ValidationError as e:
                raise falcon.HTTPBadRequest(
                    'Request data failed validation',
                    description=e.message
                )

        result = func(self, req, resp, *args, **kwargs)

        if resp_schema is not None:
            try:
                jsonschema.validate(
                    resp.media, resp_schema,
                    format_checker=jsonschema.FormatChecker()
                )
            except jsonschema.ValidationError:
                raise falcon.HTTPInternalServerError(
                    'Response data failed validation'
                    # Do not return 'e.message' in the response to
                    # prevent info about possible internal response
                    # formatting bugs from leaking out to users.
                )

        return result

    return wrapper


def _validate_async(func, req_schema=None, resp_schema=None):
    @wraps(func)
    async def wrapper(self, req, resp, *args, **kwargs):
        if req_schema is not None:
            m = await req.get_media()

            try:
                jsonschema.validate(
                    m, req_schema,
                    format_checker=jsonschema.FormatChecker()
                )
            except jsonschema.ValidationError as e:
                raise falcon.HTTPBadRequest(
                    'Request data failed validation',
                    description=e.message
                )

        result = await func(self, req, resp, *args, **kwargs)

        if resp_schema is not None:
            try:
                jsonschema.validate(
                    resp.media, resp_schema,
                    format_checker=jsonschema.FormatChecker()
                )
            except jsonschema.ValidationError:
                raise falcon.HTTPInternalServerError(
                    'Response data failed validation'
                    # Do not return 'e.message' in the response to
                    # prevent info about possible internal response
                    # formatting bugs from leaking out to users.
                )

        return result

    return wrapper
