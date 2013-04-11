==============
Error Handling
==============

Error handling in starflyer is done via error handlers which you have to register on the application object::

    from notfound import NotFoundHandler
    from internalerror import InternalServerErrorHandler

    class MyApp(Application):

        error_handlers = {
            404:    NotFoundHandler,
            500:    InternalServerErrorHandler,
        }

If a HTTP exception with that code is raised then the respective handler is called.
The 500 error is different in that it is also called if non HTTP exceptions are raised. 
These are also automatically logged.


Error Handlers
==============

Error handlers instances of the starflyer ``Handler`` class. An error handler can look as follows::

    class NotFoundHandler(Handler):

        template = "notfound.html"
        
        def get(self):
            """show the error"""
            self.render()

You also have access to the failed request inside e.g. in order to inspect the URL or other data.
Moreover this request has an ``exception`` attribute which has the exception object attached. 

If an error handler raises an exception then this will return a plain 500 error response.
