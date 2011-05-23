"""
exceptions to be used in handlers for returning errors and still being able
to pass in a customizable payload
"""

import werkzeug.wrappers
import werkzeug.exceptions

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
        






