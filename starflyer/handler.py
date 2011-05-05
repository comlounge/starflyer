import os
import copy
import json
from paste.fileapp import FileApp
import werkzeug.exceptions
from paste.auth import auth_tkt
from decorators import ashtml

class Handler(object):
    """a request handler which is also the base class for an application"""

    template="" # default template to use
    
    def __init__(self, app=None, request=None, settings={}, log=None):
        """initialize the Handler with the calling application and the request
        it has to handle."""
        
        self.app = app
        self.request = request
        self.settings = settings
        self.log = log
        self.prepare() # hook for handling auth etc.

    def prepare(self):
        """overwrite this method if you need auth handling etc."""
        pass

    def prepare_render(self, data):
        """here you can adjust template vars before they get rendered"""
        return data

    @ashtml()
    def render(self, tmplname=None, values={}, errors={}, **kwargs):
        """render a template. If the ``tmplname`` is given, it will render
        this template otherwise take the default ``self.template``. You can
        pass in kwargs which are then passed to the template on rendering."""
        if tmplname is None:
            tmplname = self.template
        data = copy.copy(kwargs)
        data = self.prepare_render(data)
        data['values'] = values
        data['errors'] = errors
        tmpl = self.settings.pts.get_template(tmplname)
        return tmpl.render(**data)

    def redirect(self, location):
        """redirect to ``location``"""
        return werkzeug.redirect(location=location)

    def handle(self, **m):
        """handle a single request. This means checking the method to use, looking up
        the method for it and calling it. We have to return a WSGI application"""
        method = self.request.method
        method = self.request.values.get("method", method)
        method = method.lower()
        if hasattr(self, method):
            self.log.debug("calling method %s on handler '%s' " %(self.request.method, m['handler']))
            del m['handler']
            return getattr(self, method)(**m)
        else:
            return werkzeug.exceptions.MethodNotAllowed()
        
