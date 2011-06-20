import werkzeug
import routes
from logbook import Logger, FileHandler, NestedSetup, Processor
from werkzeug.routing import Map, Rule, NotFound, Submount, RequestRedirect

import handler


class Mapper(object):
    """a mapper which is able to map url routes to handlers"""

    def __init__(self):
        self.url_map = Map()
        self.views = {}

    def add(self, path, endpoint, handler):
        self.url_map.add(Rule(path, endpoint=endpoint))
        self.views[endpoint] = handler

    def map(self, environ):
        """maps an environment to a handler. Returns the handler object
        and the args. If it does not match, ``(None, None)`` is returned.
        """
        urls = self.url_map.bind_to_environ(environ)
        endpoint, args = urls.match()
        return self.views.get(endpoint, None), args

    def generator(self, environ):
        return self.url_map.bind_to_environ(environ)

    def add_submapper(self, submapper):
        """attach a submapper to us"""
        self.url_map.add(submapper.url_map)
        self.views.update(submapper.views)


class Submapper(object):
    """a mapper for sub modules which mainly delegates"""

    def __init__(self, path):
        self.url_map = Submount(path, [])
        self.views = {}

    def add(self, path, endpoint, handler):
        self.add_rule(Rule(path, endpoint=endpoint))
        self.add_view(endpoint, handler)

    def add_rule(self, rule):
        """add a Rule instance to the map"""
        self.url_map.rules.append(rule)

    def add_view(self, endpoint, handler):
        """add a mapping between one endpoint and a handler"""
        self.views[endpoint] = handler


class Application(object):
    """a base class for dispatching WSGI requests"""
    
    def __init__(self, settings={}, prefix=""):
        """initialize the Application with a settings dictionary and an optional
        ``prefix`` if this is a sub application"""
        self.settings = settings
        self.view_mappings = {} # endpoint -> handler
        self.url_map = Mapper()
        self.mapper = routes.Mapper()
        self.setup_handlers(self.mapper)
        self.loghandler = self.setup_logger()

    def add_rule(self, path, endpoint, handler):
        """add a rule to the view mapper"""
        self.url_map.add(path, endpoint, handler)

    def __call__(self, environ, start_response):
        request = werkzeug.Request(environ)
        
        try:
            handler_cls, args = self.url_map.map(environ)
        except RequestRedirect, e:
            return e(environ, start_response)
        except NotFound:
            return werkzeug.exceptions.NotFound()(environ, start_response)

        handler = handler_cls(app=self, 
                    request=request, 
                    settings=self.settings, 
                    args = args,
                    log=Logger(self.settings.log_name),
                    url_generator = self.url_map.generator(environ))
        
        def inject(record):
            """the injection callback for any log record"""
            record.extra['handler'] = str(m['handler'])
            record.extra['url'] = request.url
            record.extra['method'] = request.method
            record.extra['ip'] = request.remote_addr

            # TODO: add a hook for adding more information

        with Processor(inject):
            with self.loghandler.threadbound():
                try:
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
        
