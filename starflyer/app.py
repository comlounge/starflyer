import werkzeug
import pkg_resources
from logbook import Logger, FileHandler, NestedSetup, Processor
from werkzeug.routing import Map, Rule, NotFound, Submount, RequestRedirect

import handler

class Application(object):
    """a base class for dispatching WSGI requests"""
    
    def __init__(self, config):
        """initialize the Application 

        :param config: a ``Configuration`` instance
        """
        self.config = config
        self.settings = config.settings

    def __call__(self, environ, start_response):
        request = werkzeug.Request(environ)
        
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

def run(global_config, **local_config):
    """run the application"""
    group = 'starflyer.config'
    entrypoint = list(pkg_resources.iter_entry_points(group=group, name="default"))[0]
    setup = entrypoint.load()
    # TODO: take ini file into account
    config = setup(**local_config)
    app = config.app(config)
    if local_config.get('development', 'false').lower() == 'true':
        from werkzeug.debug import DebuggedApplication
        app = DebuggedApplication(app)
    return werkzeug.wsgi.SharedDataMiddleware(app, config._static_map)


