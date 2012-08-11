# -*- coding: utf-8 -*-
"""
exceptions to be used in handlers for returning errors and still being able
to pass in a customizable payload

this is partly flask and partly own code
"""

__all__ = ['ConfigurationError']

import werkzeug.wrappers
import werkzeug.exceptions
from .helpers import json


class StarflyerException(Exception):
    """Base class for starflyer exceptions"""

    def __init__(self, msg):
        """initialize the exception"""
        self.msg = msg

    def __repr__(self):
        return """<%s : %s>""" %(self.__class__.__name__, self.msg)

    __str__ = __repr__

class ConfigurationError(StarflyerException):
    """something went wrong during the configuration phase"""


class Redirect(werkzeug.exceptions.HTTPException):
    """a redirect"""

    def __init__(self, location, code=302):
        self.display_location = location
        if isinstance(location, unicode):
            from werkzeug.urls import iri_to_uri
            location = iri_to_uri(location)
        self.location = location
        self.code = code
        self.response = self._get_response()
        
    def get_response(self, environ):
        return self.response

    def _get_response(self):
        """return the response"""
        response = werkzeug.wrappers.Response(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            '<title>Redirecting...</title>\n'
            '<h1>Redirecting...</h1>\n'
            '<p>You should be redirected automatically to target URL: '
            '<a href="%s">%s</a>.  If not click the link.' %
            (self.location, self.display_location), self.code, mimetype='text/html')
        response.headers['Location'] = self.location
        return response
        

class JSONHTTPException(werkzeug.exceptions.HTTPException):
    """A base class for HTTP exceptions with ``Content-Type:
    application/json``.

    The ``description`` attribute of this class must set to a string (*not* an
    HTML string) which describes the error.

    """

    def get_body(self, environ):
        """Overrides :meth:`werkzeug.exceptions.HTTPException.get_body` to
        return the description of this error in JSON format instead of HTML.

        """
        return json.dumps(dict(description=self.get_description(environ)))

    def get_headers(self, environ):
        """Returns a list of headers including ``Content-Type:
        application/json``.

        """
        return [('Content-Type', 'application/json')]


class JSONBadRequest(JSONHTTPException, werkzeug.exceptions.BadRequest):
    """Represents an HTTP ``400 Bad Request`` error whose body contains an
    error message in JSON format instead of HTML format (as in the superclass).

    """

    #: The description of the error which occurred as a string.
    description = (
        'The browser (or proxy) sent a request that this server could not '
        'understand.'
    )






