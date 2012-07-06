import werkzeug
import pkg_resources
import urlparse
import copy
import os
from logbook import Logger, FileHandler, NestedSetup, Processor
import wrappers
import werkzeug
import werkzeug.routing as routing

from .sessions import SecureCookieSessionInterface
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

    # directory and URL endpoint setup
    template_dir = "templates/"
    static_dir = "static/"
    static_url = "static/"

    # class to be used for URL Routes
    url_rule_class = routing.Rule

    # session interface
    session_interface = SecureCookieSessionInterface()

    # response class to use
    response_class = wrappers.Response

    # debug or not
    debug = False

    def __init__(self, config={}, **kw):
        """initialize the Application 

        :param config: a dictionary of configuration values
        """

        self.url_map = routing.Map()
        self.handlers = {}

        self.config = copy.copy(self.defaults)
        self.config.update(config)
        self.config.update(kw)
        self.config = AttributeMapper(self.config)

        # TODO: enforce attributes somehow? 
        if "secret_key" not in self.config:
            self.config.secret_key = None

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


    def raise_routing_exception(self, e):
        """raise a routing exception"""
        raise e

        

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



    ####
    #### request processing
    ####

    def check_first_request(self, request):
        """check if we have already run the hooks for the first request. If not, do so now"""
        if not self._got_first_request:
            self.before_first_request(request)
            self._got_first_request = True

    def __call__(self, environ, start_response):
        """do WSGI request dispatching"""

        # first thing is to actually create the request as we need it anyway
        request = wrappers.Request(environ)

        # create the url adapter
        urls = self.url_map.bind_to_environ(environ)

        # check if we are the first request ever for this application
        self.check_first_request(request)

        # now try to match the request to an endpoint and a handler
        try:
            url_rule, request.view_args = urls.match(return_rule=True)
            request.url_rule = url_rule
        except werkzeug.exceptions.HTTPException, e:
            request.routing_exception = e
            self.raise_routing_exception(e)

        # try to find the right handler for this url and instantiate it
        handler = self.handlers[url_rule.endpoint](self, request, urls)

        # now process the request via the handler
        rv = handler(**request.view_args) # this needs to be a Response object
        rv = self.finalize_response(rv) # hook for post processing a resposne
        return rv(environ, start_response)


        
        try:
            handler_cls, args = self.config._url_map.map(environ)
        except RequestRedirect, e:
            return e(environ, start_response)
        except NotFound:
            return werkzeug.exceptions.NotFound()(environ, start_response)

        def inject(record):
            """the injection callback for any log record"""
            record.extra['handler'] = str(handler_cls)
            record.extra['url'] = request.url
            record.extra['method'] = request.method
            record.extra['ip'] = request.remote_addr
            record.extra['ip'] = request.remote_addr
            record.hid = id(request)
            # TODO: add a hook for adding more information

        with Processor(inject):
            log_name = self.settings.get("log_name", "")
            with self.config.log_handler.threadbound():
                try:
                    handler = handler_cls(app=self, 
                                request=request, 
                                config=self.config, 
                                args = args,
                                log=Logger(log_name),
                                url_generator = self.config._url_map.generator(environ))
                    return handler.handle(**args)(environ, start_response)
                except werkzeug.exceptions.HTTPException, e:
                    return e(environ, start_response)

    def setup_logger(self):
        """override this method to define your own log handlers. Usually it
        will return a ``NestedSetup`` object to be used"""

        handler = FileHandler(self.settings.log_filename, bubble=True)
        return NestedSetup([
            handler,
        ])

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


def run(global_config, **local_config):
    """run the application"""
    group = 'starflyer.config'
    entrypoint = list(pkg_resources.iter_entry_points(group=group, name="default"))[0]
    setup = entrypoint.load()

    # TODO: take ini file into account
    config = setup(**local_config)

    # run additional configurators
    for cf_entrypoint in local_config.get("configurators", "").split(" "):
        parts = urlparse.urlparse(cf_entrypoint)
        if parts.scheme!="egg":
            continue
        if "#" in parts.path:
            package, name = parts.path.split("#") 
        else:
            package = parts.path
            name = "default"
        entry = pkg_resources.get_entry_info(package, "starflyer.config", name)
        setup_func = entry.load()
        config = setup_func(config)

    app = config.app(config)
    if local_config.get('development', 'false').lower() == 'true':
        from werkzeug.debug import DebuggedApplication
        app = DebuggedApplication(app)
    return werkzeug.wsgi.SharedDataMiddleware(app, config._static_map)


