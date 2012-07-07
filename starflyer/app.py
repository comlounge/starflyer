import pkg_resources
import urlparse
import datetime
import copy
import os
import sys

import logbook
import wrappers
import werkzeug

import sessions
from . import AttributeMapper

class URL(object):
    """proxy object for a URL rule in order to be used more easily in route listings"""

    def __init__(self, path, endpoint = None, handler = None, **options):
        """initialize the route url basically with what we need for werkzeug routes"""
        self.path = path
        self.endpoint = endpoint
        self.handler = handler
        self.options = options


class Application(object):
    """a base class for dispatching WSGI requests"""
    
    defaults = {
        'secret_key' : os.urandom(24)
    }

    routes = [] # list of rules
    handlers = {} # mapping from endpoint to handler classes
    error_handlers = {} # mapping from error code to error handler classes

    # directory and URL endpoint setup
    template_dir = "templates/"
    static_dir = "static/"
    static_url = "static/"

    # class to be used for URL Routes
    url_rule_class = werkzeug.routing.Rule

    # session interface
    session_interface = sessions.SecureCookieSessionInterface()

    # response class to use
    response_class = wrappers.Response

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
        'propagate_exceptions'          : None,
        'debug'                         : False,
        'testing'                       : False,
    }


    def __init__(self, config={}, **kw):
        """initialize the Application 

        :param config: a dictionary of configuration values
        """

        self.url_map = werkzeug.routing.Map()
        self.handlers = {}

        self.config = AttributeMapper(self.enforced_defaults or {})
        self.config.update(self.defaults)
        self.config.update(config)
        self.config.update(kw)

        # TODO: update from environment vars?
        
        for route in self.routes:
            self.add_url_rule(
                route.path,
                route.endpoint,
                route.handler,
                **route.options)

        # we did not have any request yet
        self._got_first_request = False
    
    
    ####
    #### hooks for first request, finalizing and error handling
    ####

    def before_first_request(self, request):
        """if you want to run something on the first incoming request then put it here"""
        pass


    def finalize_response(self, response):
        """with this hook you can do something very generic to a response after all processing."""
        return response


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
    
    def add_url_rule(self, path, endpoint = None, handler = None, **options):
        """add another url rule to the url map""" 
        if endpoint is None:
            assert handler is not None, "handler and endpoint not provided"
            endpoint = handler.__name__
        options['endpoint'] = endpoint
        options['defaults'] = options.get('defaults') or None

        rule = self.url_rule_class(path, **options)
        self.url_map.add(rule)
        if handler is not None:
            self.handlers[endpoint] = handler

    @property
    def propagate_exceptions(self):
        """Returns the value of the `propagate_exceptions` configuration
        value in case it's set, otherwise a sensible default is returned.
        """
        print 1
        rv = self.config.propagate_exceptions
        print rv
        if rv is not None:
            return rv
        return self.config.testing or self.config.debug


    ####
    #### request processing
    ####

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
        urls = self.url_map.bind_to_environ(environ)

        try:
            url_rule, request.view_args = urls.match(return_rule=True)
            request.url_rule = url_rule
        except werkzeug.exceptions.HTTPException, e:
            # this basically means 404 but maybe some debugging can occur
            # this is reraised then though
            self.raise_routing_exception(request, e)

        # try to find the right handler for this url and instantiate it
        return self.handlers[url_rule.endpoint](self, request, urls)


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
        with logbook.Processor(inject):
            try:
                # find the handler and call it
                handler = self.find_handler(request)
                response = handler(**request.view_args)
            except Exception, e:
                response = self.handle_user_exception(request, e)

        if not self.session_interface.is_null_session(handler.session):
            self.save_session(handler.session, response)

        return self.finalize_response(response) # hook for post processing a resposne

    
    def __call__(self, environ, start_response):
        """do WSGI request dispatching"""
        request = wrappers.Request(environ)
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
        if handlers and e.code in self.error_handlers:
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
           or not isinstance(request.routing_exception, werkzeug.exceptions.RequestRedirect) \
           or request.method in ('GET', 'HEAD', 'OPTIONS'):
            raise exception

        from .helpers import FormDataRoutingRedirect
        raise FormDataRoutingRedirect(request, exception)


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

           Flask will suppress any server error with a generic error page
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



