import os
import copy
import json
import werkzeug.exceptions
import exceptions
import datetime
import starflyer
import sessions

class Handler(object):
    """a request handler which is also the base class for an application"""

    template="" # default template to use
    use_hooks = True # set to False if you don't want the before_handler hooks to be used for this handler
    
    def __init__(self, app, request, module = None):
            
        """initialize the Handler with the calling application and the request
        it has to handle.
        
        :param app: The ``Application`` instance this handler belongs to
        :param request: The request object
        :param module: The module from which we might have been called. ``None`` if it was the main app
        """
        
        self.app = app
        self.request = request
        self.module = module
        self.config = app.config
        self.url_adapter = request.url_adapter
        self.flashes = None
        self.session = None

        # retrieve a session if available
        self.session = self.app.open_session(self.request)
        if self.session is None:
            self.session = self.app.make_null_session()
        # note that session saving is happening in the app as some hooks could run before that 

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

    def flash(self, msg, category="info"):
        """add a new flash message

            (copied nearly verbatim from flask) 
            :param msg: the message to be flashed.
            :param category: the category for the message.  The following values
                are recommended: ``'message'`` for any kind of message,
                ``'error'`` for errors, ``'info'`` for information
                messages and ``'warning'`` for warnings.  However any
                kind of string can be used as category.
        """
        flashes = self.session.get('_flashes', [])
        flashes.append((category, unicode(msg)))
        self.session['_flashes'] = flashes

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
        flashes = session.pop('_flashes') if '_flashes' in session else []
        if category_filter:
            flashes = filter(lambda f: f[0] in category_filter, flashes)
        if not with_categories:
            return [x[1] for x in flashes]
        return flashes

    ####
    #### i18n MANAGEMENT
    ####
    
    def _(self, s, **kw):
        """dummy method for "translating" messages by simply passing them through. This is usally
        replaced on the fly by modules such as ``sf-babel``.

        :param s: string to translate
        """
        return s

    ####
    #### URL MANAGEMENT
    ####

    def url_for(self, endpoint = None,  _full = False, _append=False, **kwargs):
        """return a URL generated from the mapper"""
        if endpoint[0] == ".": # we might be in a module with a relative path
            if self.module is not None:
                endpoint = "%s.%s" %(self.module.name, endpoint[1:])
            else:
                endpoint = endpoint[1:] # remove dot if module not found
        return self.request.url_adapter.build(
                endpoint, 
                kwargs, 
                force_external = _full, 
                append_unknown = _append)


    ####
    #### RENDER RELATED
    ####

    @property
    def default_render_context(self):
        """return the default template rendering environment. This is the starting point
        and any additional property or method like ``render_context`` will update this
        dictionary. 
        """
        return dict(
            handler = self,
            request = self.request,
            session = self.session,
            url_for = self.url_for,
            config = self.config,
            get_flashes = self.get_flashes,
            gettext = lambda x: x                   # dummy i18n handler for jinja2
        )

    @property
    def template_globals(self):
        """return global variables to be used inside a template. Note that these are cached!"""
        return dict(
            url_for = self.url_for,
            M = self.app.module_map
        )

    @property
    def render_context(self):
        """provide attributes to a to template to be rendered by adding
        it to the provided ``params`` dictionary and returning it.
        """
        return dict()


    def render(self, tmplname=None, **kwargs):
        """render a template. If the ``tmplname`` is given, it will render
        this template otherwise take the default ``self.template``. You can
        pass in kwargs which are then passed to the template on rendering."""
        if tmplname is None:
            tmplname = self.template

        params = starflyer.AttributeMapper(self.default_render_context)
        for module in self.app.modules:
            params.update(module.get_render_context(self))
        params.update(self.app.get_render_context(self))
        params.update(self.render_context)
        params.update(kwargs)

        # if we are called from a module, we try the module prefix for loading the template
        if self.module is not None:
            # construct relative path which also allows for .. and /
            path = os.path.normpath(os.path.join("_m", self.module.name, tmplname))
            tmpl = self.app.jinja_env.get_or_select_template(path, globals = self.template_globals)
        else:
            tmpl = self.app.jinja_env.get_or_select_template(tmplname, globals = self.template_globals)
        return tmpl.render(**params)

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
    
