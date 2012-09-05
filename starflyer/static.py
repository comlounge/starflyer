from .handler import Handler
import os
import mimetypes
import time
import pkg_resources

from werkzeug.datastructures import Headers

try:
    from werkzeug.wsgi import wrap_file
except ImportError:
    from werkzeug.utils import wrap_file

class StaticFileHandler(Handler):
    """handles static files"""


    def get(self, filename=None):
        """return a static file"""

        fp = pkg_resources.resource_stream(self.app.import_name, os.path.join(self.app.static_folder, filename))

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
            
