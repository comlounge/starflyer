import werkzeug
import routes
from logbook import Logger, FileHandler, NestedSetup, Processor

import handler


class Application(object):
    """a base class for dispatching WSGI requests"""
    
    def __init__(self, settings={}, prefix=""):
        """initialize the Application with a settings dictionary and an optional
        ``prefix`` if this is a sub application"""
        self.settings = settings
        self.mapper = routes.Mapper()
        self.setup_handlers(self.mapper)
        self.loghandler = self.setup_logger()

    def __call__(self, environ, start_response):
        request = werkzeug.Request(environ)
        m = self.mapper.match(environ = environ)
        url_generator = routes.util.URLGenerator(self.mapper, environ)

        if m is not None:
            handler = m['handler'](app=self, 
                    request=request, 
                    settings=self.settings, 
                    log=Logger(self.settings.log_name),
                    url_generator = url_generator)
            
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
                        return handler.handle(**m)(environ, start_response)
                    except werkzeug.exceptions.HTTPException, e:
                        return e(environ, start_response)
        # no view found => 404
        return werkzeug.exceptions.NotFound()(environ, start_response)
        
    def setup_logger(self):
        """override this method to define your own log handlers. Usually it
        will return a ``NestedSetup`` object to be used"""

        handler = FileHandler(self.settings.log_filename, bubble=True)
        return NestedSetup([
            handler,
        ])
        
