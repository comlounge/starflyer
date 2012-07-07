import os
import copy
import json
import werkzeug.exceptions
import exceptions
import starflyer

class Handler(object):
    """a request handler which is also the base class for an application"""

    template="" # default template to use
    
    def __init__(self, app, request):
            
        """initialize the Handler with the calling application and the request
        it has to handle.
        
        :param app: The ``Application`` instance this handler belongs to
        :param request: The request object
        :param url_adapter: The url mapper in use 
        """
        
        self.app = app
        self.request = request
        self.config = app.config
        self.url_adapter = request.url_adapter
        self.flashes = None
        self.session = None

        # retrieve a session if available
        self.session = self.app.open_session(self.request)
        if self.session is None:
            self.session = self.app.make_null_session()


    ####
    #### before and after request hooks
    ####

    def before(self):
        """This method will be called before the request will be processed.
        You can override it in order to do your own processing before the 
        actual handler logic is processed. If you return a response value 
        (a String, Response, etc.) then processing is stopped and the handler
        logic is not called but instead the Response is returned directly.
        """
        pass

    def after(self, response):
        """This is the hook for response post processing. 

        This method will be called before the request will be processed.
        You can override it in order to do your own processing before the 
        actual handler logic is processed. If you return a response value 
        (a String, Response, etc.) then processing is stopped and the handler
        logic is not called but instead the Response is returned directly.
        """
        return response


    ### TODO: what about changing the Response during the handler?
    ### right now we have an existing one already but what if we want
    ### to change headers? Do it via decorators only? Maybe better, also for
    ### testing.

    ####
    #### FLASH MANAGING
    ####

    def flash(self, msg, category="message"):
        """add a new flash message

            (copied nearly verbatim from flask)

            :param msg: the message to be flashed.
            :param category: the category for the message.  The following values
                are recommended: ``'message'`` for any kind of message,
                ``'error'`` for errors, ``'info'`` for information
                messages and ``'warning'`` for warnings.  However any
                kind of string can be used as category.
        """
        flashes = self.session.get('flashes', [])
        flashes.append((category, msg))
        self.session['flashes'] = flashes

    def get_flashes(self, with_categories=False, category_filter=[]):
        """Pulls all flashed messages from the session and returns them.
        Further calls in the same request to the function will return
        the same messages.  By default just the messages are returned,
        but when `with_categories` is set to `True`, the return value will
        be a list of tuples in the form ``(category, message)`` instead.
    
        Filter the flashed messages to one or more categories by providing those
        categories in `category_filter`.  This allows rendering categories in
        separate html blocks.  The `with_categories` and `category_filter`
        arguments are distinct:
    
        * `with_categories` controls whether categories are returned 
            with message text (`True` gives a tuple, where `False` 
            gives just the message text).
        * `category_filter` filters the messages down to only those 
            matching the provided categories.
    
        :param with_categories: set to `True` to also receive categories.
        :param category_filter: whitelist of categories to limit return values

        (copied somewhat verbatim from flask)
        """        
    
        session = self.session
        flashes = session.pop('flashes') if 'flashes' in session else []
        if category_filter:
            flashes = filter(lambda f: f[0] in category_filter, flashes)
        if not with_categories:
            return [x[1] for x in flashes]
        return flashes

    def url_for(self, name, _full = False, _append=False, **kwargs):
        """return a URL generated from the mapper"""
        return self.url_adapter.build(
                name, 
                kwargs, 
                force_external = _full, 
                append_unknown = _append)

    ####
    #### RENDER RELATED
    ####

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
        params['settings'] = self.config.settings
        params['errors'] = errors
        params['url'] = self.request.path
        params['url_for'] = self.url_for
        params['snippets'] = self.config.snippets
        params['flash_messages'] = self.messages_in+self.messages_out
        self.messages_out = []
        tmpl = self.config.templates.main.get_template(tmplname)
        return tmpl.render(**params)

    def redirect(self, location, code=302, cookies={}):
        """redirect to ``location``"""
        redirect = exceptions.Redirect(location, code=code)
        redirect.response.set_cookie('m', self._encode_messages(self.messages_out))
        for a,v in cookies.items():
            redirect.response.set_cookie(a, v)
        return redirect

        
    def __call__(self, **m):
        """handle a single request. This means checking the method to use,
        looking up the method for it and calling it. We have to return a WSGI
        application"""
        
        method = self.request.method
        method = self.request.values.get("method", method)
        method = method.lower()

        # if method is not present in handler, return Method Not Allowed
        if not hasattr(self, method):
            return werkzeug.exceptions.MethodNotAllowed()

        rv = self.before()
        if rv is None:
            # call the handler only if we not already have a response value
            rv = getattr(self, method)(**m)

        # create the response
        response = self.make_response(rv) 

        # return the post processed response
        return self.after(response)


    def make_response(self, rv):
        """Converts the return value from a handler to a real
        response object that is an instance of :attr:`app.response_class`.

        The following types are allowed for `rv`:

        .. tabularcolumns:: |p{3.5cm}|p{9.5cm}|

        ======================= ===========================================
        :attr:`response_class`  the object is returned unchanged
        :class:`str`            a response object is created with the
                                string as body
        :class:`unicode`        a response object is created with the
                                string encoded to utf-8 as body
        a WSGI function         the function is called as WSGI application
                                and buffered as response object
        :class:`tuple`          A tuple in the form ``(response, status,
                                headers)`` where `response` is any of the
                                types defined here, `status` is a string
                                or an integer and `headers` is a list of
                                a dictionary with header values.
        ======================= ===========================================

        :param rv: the return value from the view function

        """
        status = headers = None
        if isinstance(rv, tuple):
            rv, status, headers = rv + (None,) * (3 - len(rv))

        if rv is None:
            raise ValueError('Handler did not return a response')

        if not isinstance(rv, self.app.response_class):
            # When we create a response object directly, we let the constructor
            # set the headers and status.  We do this because there can be
            # some extra logic involved when creating these objects with
            # specific values (like defualt content type selection).
            if isinstance(rv, basestring):
                rv = self.app.response_class(rv, headers=headers, status=status)
                headers = status = None
            else:
                rv = self.app.response_class.force_type(rv, self.request.environ)

        if status is not None:
            if isinstance(status, basestring):
                rv.status = status
            else:
                rv.status_code = status
        if headers:
            rv.headers.extend(headers)

        return rv
    
