import werkzeug
import routes
from logbook import Logger
from logbook import FileHandler, NestedSetup, NullHandler, MailHandler, Processor

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
        #self.loghandler = FileHandler(self.logfilename)

    def __call__(self, environ, start_response):
        with self.loghandler.threadbound():
            request = werkzeug.Request(environ)
            m = self.mapper.match(environ = environ)
            if m is not None:
                handler = m['handler'](app=self, request=request, settings=self.settings, log=Logger(self.settings.log_name))
                try:
                    return handler.handle(**m)(environ, start_response)
                except werkzeug.exceptions.HTTPException, e:
                    return e(environ, start_response)
            # no view found => 404
            return werkzeug.exceptions.NotFound()(environ, start_response)
        
    def setup_logger(self):
        return NestedSetup([
            FileHandler(self.settings.log_filename),
        ])
        
