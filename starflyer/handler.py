import os
import copy
import json
from paste.fileapp import FileApp
import werkzeug.exceptions
from paste.auth import auth_tkt
from decorators import ashtml
from werkzeug.contrib.securecookie import SecureCookie
import exceptions
import starflyer

class Handler(object):
    """a request handler which is also the base class for an application"""

    template="" # default template to use
    
    def __init__(self, 
            app=None, 
            request=None, 
            settings={}, 
            args = {},
            log=None, 
            url_generator=None):
        """initialize the Handler with the calling application and the request
        it has to handle.
        
        :param app: The ``Application`` instance this handler belongs to
        :param request: The request object
        :param settings: The global settings dict
        :param args: The arguments returned by the matched route
        :param log: A logbook ``Logger`` instance 
        :param url_generator: The url generator we use 
        """
        
        self.app = app
        self.request = request
        self.settings = settings
        self.log = log            
        self.args = args
        self.url_generator = url_generator
        self.messages_out = []
        self.messages_in = []
        self.response = werkzeug.wrappers.Response()
        self.prepare() # hook for handling auth etc.

    def prepare(self):
        """overwrite this method if you need auth handling etc. This method
        will be called before calling the actual method. You can set here
        additional instance variable etc. if you need them and you have access
        to ``self.request``, ``self.settings`` and ``self.app``."""
        pass

    def url_for(self, name, force_external = False, append_unknown=False, **kwargs):
        """return a URL generated from the mapper"""
        return self.url_generator.build(name, kwargs, force_external = force_external, append_unknown=append_unknown)

    def prepare_render(self, params):
        """provide attributes to a to template to be rendered by adding
        it to the provided ``params`` dictionary and returning it.
        """
        return params
    
    def render(self, tmplname=None, values={}, errors={}, **kwargs):
        """render a template. If the ``tmplname`` is given, it will render
        this template otherwise take the default ``self.template``. You can
        pass in kwargs which are then passed to the template on rendering."""
        if tmplname is None:
            tmplname = self.template

        params = starflyer.AttributeMapper()
        params.update(kwargs)
        params = self.prepare_render(params)
        params['values'] = values
        params['errors'] = errors
        params['url'] = self.request.path
        params['url_for'] = self.url_for
        params['flash_messages'] = self.messages_in+self.messages_out
        self.messages_out = []
        tmpl = self.settings.templates.get_template(tmplname)
        return tmpl.render(**params)

    def redirect(self, location, code=302, cookies={}):
        """redirect to ``location``"""
        redirect = exceptions.Redirect(location, code=code)
        redirect.response.set_cookie('m', self._encode_messages(self.messages_out))
        for a,v in cookies.items():
            redirect.response.set_cookie(a, v)
        return redirect
        
    def handle(self, **m):
        """handle a single request. This means checking the method to use, looking up
        the method for it and calling it. We have to return a WSGI application"""
        method = self.request.method
        method = self.request.values.get("method", method)
        method = method.lower()

        # if method is not present in handler, return Method Not Allowed
        if not hasattr(self, method):
            return werkzeug.exceptions.MethodNotAllowed()

        # decode messages for transfer
        self.messages_in = self._decode_messages(self.request.cookies)
        #self.log.debug("calling method %s on handler '%s' " %(self.request.method, m['handler']))
        #del m['handler']

        # call the handler
        getattr(self, method)(**m)

        # we assume that the method changes the response in place
        # it might alternatively call an exception so we don't reach the
        # return 
        return self.response

    #
    # message encoding/decoding        
    #
    
    def flash(self, msg, **kwargs):
        data = {'msg' : msg}
        data.update(kwargs)
        self.messages_out.append(data)
   
    def _decode_messages(self, cookies):
        if cookies.has_key('m'):
            m = SecureCookie.unserialize(cookies['m'], self.settings.cookie_secret)
            return m.get('msg', [])
        return []
    
    def _encode_messages(self, messages):
        c = SecureCookie({'msg': messages}, self.settings.cookie_secret)
        return c.serialize()
