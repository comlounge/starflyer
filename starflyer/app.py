import pkg_resources
import urlparse
import datetime
import copy
import os
import sys

import logbook
import wrappers
import werkzeug
import werkzeug.test
from werkzeug.contrib.securecookie import SecureCookie
import jinja2

from werkzeug.datastructures import ImmutableDict
from wsgiref.util import shift_path_info
from werkzeug.test import Client, EnvironBuilder

import sessions
import static
import exceptions
from helpers import AttributeMapper, URL
from templating import DispatchingJinjaLoader

class Application(object):
    """a base class for dispatching WSGI requests"""

    defaults = {}

    routes = [] # list of rules
    error_handlers = {} # mapping from error code to error handler classes

    handlers = {} # mapping from endpoint to handler classes

    # class to be used for URL Routes
    url_rule_class = werkzeug.routing.Rule

    # session interface
    session_interface = sessions.SecureCookieSessionInterface()

    # class to be used as test client class
    test_client_class = None

    # response class to use
    response_class = wrappers.Response
    request_class = wrappers.Request

    # enforeced defaults (these have to be existent in the config
    # for starflyer to work (DO NOT CHANGE!)
    enforced_defaults = {
        'session_cookie_name'           : "s",
        'secret_key'                    : None,
        'permanent_session_lifetime'    : datetime.timedelta(days=31),
        'session_cookie_domain'         : None,
        'session_cookie_path'           : None,
        'session_cookie_httponly'       : True,
        'session_cookie_secure'         : False,
        'preferred_url_scheme'          : 'http',
        'logger_name'                   : None,
        'server_name'                   : None,
        'application_root'              : None,
        'propagate_exceptions'          : None, # this is used for testing and debugging and means to re-raise it and not use an error handler for uncaught exceptions
        'debug'                         : False,
        'testing'                       : False,
        'static_cache_timeout'          : 12 * 60 * 60,
        'template_folder'               : "templates/",
        'static_folder'                 : "static/",
        'static_url_path'               : "/static",
    }

    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_']
    )
    
    jinja_filters = ImmutableDict()

    modules = [] # list of modules
    module_map = AttributeMapper() # mapped version of modules

    def __init__(self, import_name, config={}, **kw):
        """initialize the Application 

        :param import_name: the __name__ of the module we are running under.
        :param config: a dictionary of configuration values
        """

        self.import_name = import_name

        # initialize URL mapping variables
        self.url_map = werkzeug.routing.Map()
        self.handlers = {}
       
        # initialize configuration
        self.config = AttributeMapper(self.enforced_defaults or {})
        self.config.update(self.defaults)
        self.config.update(config)
        self.config.update(kw)
        # TODO: update from environment vars?

        # initialize the actual routes 
        for route in self.routes:
            self.add_url_rule(
                route.path,
                route.endpoint,
                route.handler,
                **route.options)

        # we did not have any request yet
        self._got_first_request = False

        # clean up static url path
        if self.config.static_folder is not None:
            sup = self.config.static_url_path
            if sup.endswith("/"):
                sup = sup[:-1] # remove any trailing slash
            if not sup.startswith("/"):
                sup = "/"+sup # add a leading slash if missing
            self.add_url_rule(sup+ '/<path:filename>',
                            endpoint='static',
                            handler=static.StaticFileHandler)

        # now bind all the modules to our app and create a mapping 
        for module in self.modules:
            module.bind_to_app(self)
            self.module_map[module.name] = module

        # now call the hook for changing the setup after initialization
        self.finalize_setup()

        # for testing purposes. Set app.config.testing = True and this will be populated.
        self.last_handler = None
    
    ####
    #### hooks for first request, finalizing and error handling
    ####

    def before_first_request(self, request):
        """if you want to run something on the first incoming request then put it here"""
        pass

    def before_handler(self, handler):
        """this is run before handler processing starts but the handler is already initialized.
        You can check request, session and all that and maybe add some variables to the handler.

        If you return something else than None, handler processing will not happen and the
        return value will be taken as response instead. 
        """

    def after_handler(self, handler, response):
        """This hook is run after the handler processing is done but before the response is sent
        out. You can check the handler or response and maybe return your own response here. In case
        you do that this response will be used instead. If you return None then the original handler
        response will be used.
        """


    def finalize_response(self, response):
        """with this hook you can do something very generic to a response after all processing.

        TODO: check if this is used somewhere in our projects
        
        Please not that the response can also be an :class:`~werkzeug.exception.HTTPException` instance
        which does not have a status code. 

        TODO: Shall we only do finalize on non-exception responses?
        """
        return response

    def finalize_setup(self):
        """a hook you can use to finalize the setup. You can add new routes, change configuration
        values etc.
        """

    ####
    #### handler related hooks you can override
    ####
    
    def get_render_context(self, handler):
        """create the global app wide render context which is then passed to the template for
        rendering. Here you can pass in global variables etc. You also get the active handler
        for inspecting session, request and so on or for choosing based on the handler what to 
        pass.

        Note though that handler based parameters are probably better located in the handler itself.

        :param handler: The active handler instance
        """
        return {}

    def after_handler_init(self, handler):
        """This is called from the handler after the initialization has been finished. You
        can use this to e.g. further inspect the request and change your handler instance data

        :param handler: The handler for which the render context is computed
        """


    ####
    #### TEMPLATE related
    ####

    @property
    def jinja_loader(self):
        """create the jinja template loader for this app.

        Also modules can create those loaders and the ``create_global_jinja_loader``
        method will gather all those together. Hence we have these two functions for
        obviously doing the same thing.

        In case you want to change the loader for app templates, simply override
        this property in your subclassed app.
        """
        if self.config.template_folder is not None:
            return jinja2.PackageLoader(self.import_name, self.config.template_folder)
        return None

    @property
    def global_jinja_loader(self):
        """create the global jinja loader by collecting all the loaders of the app
        and the modules together to one big loader
        """
        return DispatchingJinjaLoader(self)


    @werkzeug.cached_property
    def jinja_env(self):
        """create the jinja environment"""
        options = dict(self.jinja_options)
        if 'loader' not in options:
            options['loader'] = self.global_jinja_loader
        #if 'autoescape' not in options:
            #options['autoescape'] = self.select_jinja_autoescape
        rv = jinja2.Environment(**options)
        for name, flt in self.jinja_filters.items():
            rv.filters[name] = flt
        return rv
        

    ####
    #### SESSION related
    #### (directly copied from flask)
    ####

    def open_session(self, request):
        """Creates or opens a new session.  Default implementation stores all
        session data in a signed cookie.  This requires that the
        :attr:`secret_key` is set.  Instead of overriding this method
        we recommend replacing the :class:`session_interface`.

        :param request: an instance of :attr:`request_class`.
        """
        return self.session_interface.open_session(self, request)


    def save_session(self, session, response):
        """Saves the session if it needs updates.  For the default
        implementation, check :meth:`open_session`.  Instead of overriding this
        method we recommend replacing the :class:`session_interface`.

        :param session: the session to be saved (a
                        :class:`~werkzeug.contrib.securecookie.SecureCookie`
                        object)
        :param response: an instance of :attr:`response_class`
        """
        return self.session_interface.save_session(self, session, response)


    def make_null_session(self):
        """Creates a new instance of a missing session.  Instead of overriding
        this method we recommend replacing the :class:`session_interface`.

        .. versionadded:: 0.7
        """
        return self.session_interface.make_null_session(self)


    ####
    #### CONFIGURATION related
    ####
    
    def add_url_rule(self, url_or_path, endpoint = None, handler = None, **options):
        """add another url rule to the url map""" 
        if isinstance(url_or_path, URL):
            path = url_or_path.path
            endpoint = url_or_path.endpoint
            handler = url_or_path.handler
            options = url_or_path.options
        else:
            path = url_or_path
        if endpoint is None:
            assert handler is not None, "handler and endpoint not provided"
            endpoint = handler.__name__
        options['endpoint'] = endpoint
        options['defaults'] = options.get('defaults') or None

        rule = self.url_rule_class(path, **options)
        self.url_map.add(rule)
        if handler is not None:
            self.handlers[endpoint] = handler


    ####
    #### request processing
    ####

    @property
    def propagate_exceptions(self):
        """Returns the value of the `propagate_exceptions` configuration
        value in case it's set, otherwise a sensible default is returned.
        """
        rv = self.config.propagate_exceptions
        if rv is not None:
            return rv
        return self.config.testing or self.config.debug

    def check_first_request(self, request):
        """check if we have already run the hooks for the first request. If not, do so now"""
        if not self._got_first_request:
            self.before_first_request(request)
            self._got_first_request = True


    def find_handler(self, request):
        """retrieve the handler for the given URL. If it is not found, a routing exception
        is raised.

        :returns:   an instance of :class:`~starflyer.Handler` 
        """

        # create the url adapter
        urls = self.url_map.bind_to_environ(request.environ)

        try:
            url_rule, request.view_args = urls.match(return_rule=True)
            request.url_rule = url_rule
            request.url_adapter = urls
        except werkzeug.exceptions.HTTPException, e:
            # this basically means 404 but maybe some debugging can occur
            # this is reraised then though
            self.raise_routing_exception(request, e)

        # check if we are called from a module
        module = None
        endpoint = url_rule.endpoint
        parts = endpoint.split(".")
        if len(parts)==2:
            module_name = parts[0]
            module = self.module_map.get(module_name, None)

        # try to find the right handler for this url and instantiate it
        return self.handlers[url_rule.endpoint](self, request, module = module)


    def process_request(self, request):
        """the main request processing. Gets a :class:`~starflyer.Request` as input and
        returns an instance of :class:`~starflyer.Response`. In case of an exception
        this will be handled as well
        """

        # check if we are the first request ever for this application
        self.check_first_request(request)

        # helper for injecting data into the log record
        def inject(record):
            """the injection callback for any log record"""
            record.extra['handler'] = str(handler_cls)
            record.extra['url'] = request.url
            record.extra['method'] = request.method
            record.extra['ip'] = request.remote_addr
            record.hid = id(request)
            # TODO: add a hook for adding more information
            
            
        # use the log context to actually call the handler
        handler = None
        with logbook.Processor(inject):
            try:
                # find the handler and call it
                handler = self.find_handler(request)
                if self.config.testing:
                    # remember the last used handler for testing purposes
                    self.last_handler = handler
                response = handler(**request.view_args)
            except Exception, e:
                response = self.handle_user_exception(request, e)

        return self.finalize_response(response) # hook for post processing a resposne

    
    def __call__(self, environ, start_response):
        """do WSGI request dispatching"""
        spi = int(self.config.get("shift_path_info", 0))
        for i in range(0,spi):
            shift_path_info(environ)
        request = self.request_class(environ)
        try:
            response = self.process_request(request)
        except Exception, e:    
            response = self.handle_exception(request, e)
        return response(environ, start_response)
        

    def setup_logger(self):
        """override this method to define your own log handlers. Usually it
        will return a ``NestedSetup`` object to be used
        """
        handler = logbook.FileHandler(self.config.log_filename, bubble=True)
        return logbook.NestedSetup([
            handler,
        ])


    ####
    #### exception handling (mostly taken from flask)
    ####

    def call_error_handler(self, handler_class, request=None, **kwargs):
        """calls an error handler with the given arguments

        error handlers are instances of :class:`~starflyer.Handler` and are
        called the same way. If a handler raises an exception themselves
        the default internal server error is used.

        :param handler_class: the Handler class to use
        :param request: The request object which was used when the exception occurred.
        :param kwargs: additional keyword arguments being passed to the ``get()`` method of
            the handler.
        """
        handler = handler_class(self, request)

        # process the request via the handler
        try:
            return handler(**kwargs)
        except Exception, e:
            logbook.exception()
            return werkzeug.exceptions.InternalServerError("we got an exception in the error handler")


    def handle_http_exception(self, request, e):
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.

        .. versionadded:: 0.3
        """
        if self.error_handlers and e.code in self.error_handlers:
            handler = self.error_handlers[e.code]
        else:
            return e
        # a handler is a normal starflyer handler which we need to call now
        # with the request and all
        return self.call_error_handler(handler, request, exception = e)

    
    def handle_user_exception(self, request, e):
        """This method is called whenever an exception occurs that should be
        handled.  A special case are
        :class:`~werkzeug.exception.HTTPException`\s which are forwarded by
        this function to the :meth:`handle_http_exception` method.  This
        function will either return a response value or reraise the
        exception with the same traceback.
        """
        exc_type, exc_value, tb = sys.exc_info()
        assert exc_value is e

        # ensure not to trash sys.exc_info() at that point in case someone
        # wants the traceback preserved in handle_http_exception.  Of course
        # we cannot prevent users from trashing it themselves in a custom
        # trap_http_exception method so that's their fault then.
        if isinstance(e, werkzeug.exceptions.HTTPException):
            return self.handle_http_exception(request, e)

        for typecheck, handler in self.error_handlers.items():
            if not isinstance(typecheck, (int, long)) and isinstance(e, typecheck):
                return self.call_error_handler(handler, request, exception = e)

        raise exc_type, exc_value, tb

    
    def handle_exception(self, request, e):
        """Default exception handling that kicks in when an exception
        occours that is not caught.  In debug mode the exception will
        be re-raised immediately, otherwise it is logged and the handler
        for a 500 internal server error is used.  If no such handler
        exists, a default 500 internal server error message is displayed.
        """
        exc_type, exc_value, tb = sys.exc_info()

        handler = self.error_handlers.get(500)

        if self.propagate_exceptions:
            # if we want to repropagate the exception, we can attempt to
            # raise it with the whole traceback in case we can do that
            # (the function was actually called from the except part)
            # otherwise, we just raise the error again
            if exc_value is e:
                raise exc_type, exc_value, tb
            else:
                raise e
        logbook.exception()
        
        if handler is None:
            return werkzeug.exceptions.InternalServerError()
        return self.call_error_handler(handler, request, exception = e)

    
    def raise_routing_exception(self, request, exception):
        """Exceptions that are recording during routing are reraised with
        this method.  During debug we are not reraising redirect requests
        for non ``GET``, ``HEAD``, or ``OPTIONS`` requests and we're raising
        a different error instead to help debug situations.

        Basically this method changes the raised exceptions to eventually something
        more useful.

        :internal:
        """
        if not self.config.debug \
           or not isinstance(exception, werkzeug.routing.RequestRedirect) \
           or request.method in ('GET', 'HEAD', 'OPTIONS'):
            raise exception

        from .helpers import FormDataRoutingRedirect
        raise FormDataRoutingRedirect(request, exception)

    ####
    #### COOKIE related 
    ####

    def load_cookie(self, request, name, secret_key = None):
        """load a secure cookie by name or return an empty cookie if not present"""
        if secret_key is None:
            secret_key = self.config.get('secret_key', None)
        return SecureCookie.load_cookie(request, name, secret_key = secret_key)


    ####
    #### WSGI runner for development
    ####

    def run(self, host=None, port=None, debug=None, **options):
        """Runs the application on a local development server.  If the
        :attr:`debug` flag is set the server will automatically reload
        for code changes and show a debugger in case an exception happened.

        If you want to run the application in debug mode, but disable the
        code execution on the interactive debugger, you can pass
        ``use_evalex=False`` as parameter.  This will keep the debugger's
        traceback screen active, but disable code execution.

        .. admonition:: Keep in Mind

           starflyer will suppress any server error with a generic error page
           unless it is in debug mode.  As such to enable just the
           interactive debugger without the code reloading, you have to
           invoke :meth:`run` with ``debug=True`` and ``use_reloader=False``.
           Setting ``use_debugger`` to `True` without being in debug mode
           won't catch any exceptions because there won't be any to
           catch.

        :param host: the hostname to listen on. Set this to ``'0.0.0.0'`` to
                     have the server available externally as well. Defaults to
                     ``'127.0.0.1'``.
        :param port: the port of the webserver. Defaults to ``5000``.
        :param debug: if given, enable or disable debug mode.
                      See :attr:`debug`.
        :param options: the options to be forwarded to the underlying
                        Werkzeug server.  See
                        :func:`werkzeug.serving.run_simple` for more
                        information.
        """
        from werkzeug.serving import run_simple
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 5000
        if debug is not None:
            self.debug = bool(debug)
        options.setdefault('use_reloader', self.debug)
        options.setdefault('use_debugger', self.debug)
        try:
            run_simple(host, port, self, **options)
        finally:
            # reset the first request information if the development server
            # resetted normally.  This makes it possible to restart the server
            # without reloader and that stuff from an interactive shell.
            self._got_first_request = False



    ####
    #### TESTING SUPPORT
    ####

    def test_client(self, use_cookies=True):
        """Creates a test client for this application.  For information
        about unit testing head over to :ref:`testing`.

        Note that if you are testing for assertions or exceptions in your
        application code, you must set ``app.defaults.testing = True`` in order
        for the exceptions to propagate to the test client.  Otherwise, the
        exception will be handled by the application (not visible to the test
        client) and the only indication of an AssertionError or other exception
        will be a 500 status code response to the test client.  
        See the :attr:`testing` attribute.  For example::

            app.config.testing = True
            client = app.test_client()

        """
        cls = self.test_client_class
        if cls is None:
            cls = Client
        return cls(self, self.response_class, use_cookies=use_cookies)
    
    def make_request(self, **options):
        """create a request based on the given options. Those options are the same
        parameters which you can give to :class:`~werkzeug.test.EnvironmentBuilder`.
        
        Most common are probably the ``path`` and ``method`` parameters

        :return: an instance of the request class configured for the application instance.
        """
        builder = werkzeug.test.EnvironBuilder(**options)
        env = builder.get_environ()
        return self.request_class(env)

    def run_request(self, **options):
        """run a request through the application. This method will run it only through
        the actual request processing and will return a ``Response`` instance and not
        a HTTP response. The WSGI stack is not used in this case.

        :param options: Options for the :class:`~werkzeug.test.EnvironBuilder`
        """
        request = self.make_request(**options)
        return self.process_request(request)

        
