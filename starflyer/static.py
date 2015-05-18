from .handler import Handler
import os
import mimetypes
import time
import pkg_resources

from werkzeug.datastructures import Headers
import werkzeug.exceptions

try:
    from werkzeug.wsgi import wrap_file
except ImportError:
    from werkzeug.utils import wrap_file

class StaticFileHandler(Handler):
    """handles static files"""

    use_hooks = False

    def __init__(self, app, request, module = None):
        self.app = app
        self.request = request
        self.module = module
        self.config = app.config
        self.url_adapter = request.url_adapter
        self.session = self.app.make_null_session()

    def __call__(self, **m):
        """simplified version of a call"""

        method = self.request.method
        method = self.request.values.get("method", method)
        method = method.lower()

        return self.make_response(self.get(**m))

    def get(self, filename=None):
        """return a static file"""
        if self.module is not None:
            try:
                fp = pkg_resources.resource_stream(self.module.import_name, os.path.join(self.module.config.static_folder, filename))
            except IOError:
                raise werkzeug.exceptions.NotFound()
            config = self.module.config
        else:
            try:
                fp = pkg_resources.resource_stream(self.app.import_name, os.path.join(self.app.config.static_folder, filename))
            except IOError:
                raise werkzeug.exceptions.NotFound()
            config = self.app.config
        
        mimetype = mimetypes.guess_type(filename)[0]
        if mimetype is None:
            mimetype = 'application/octet-stream'

        headers = Headers()
        data = wrap_file(self.request.environ, fp)

        rv = self.app.response_class(data, mimetype=mimetype, headers=headers,
                                        direct_passthrough=True)

        rv.cache_control.public = True
        cache_timeout = self.config.static_cache_timeout
        if cache_timeout is not None:
            rv.cache_control.max_age = cache_timeout
            rv.expires = int(time.time() + cache_timeout)
        return rv
            

