import types

# try to load the best simplejson implementation available.  If JSON
# is not installed, we add a failing class.
json_available = True
json = None
try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        try:
            # Google Appengine offers simplejson via django
            from django.utils import simplejson as json
        except ImportError:
            json_available = False

def _assert_have_json():
    """Helper function that fails if JSON is unavailable."""
    if not json_available:
        raise RuntimeError('simplejson not installed')


# figure out if simplejson escapes slashes.  This behavior was changed
# from one version to another without reason.
if not json_available or '\\/' not in json.dumps('/'):

    def _tojson_filter(*args, **kwargs):
        if __debug__:
            _assert_have_json()
        return json.dumps(*args, **kwargs).replace('/', '\\/')
else:
    _tojson_filter = json.dumps



####
#### debug helpers (mostly taken from flask)
####


class FormDataRoutingRedirect(AssertionError):
    """This exception is raised by starflyer in debug mode if it detects a
    redirect caused by the routing system when the request method is not
    GET, HEAD or OPTIONS.  Reasoning: form data will be dropped.
    """

    def __init__(self, request, exc):
        buf = ['A request was sent to this URL (%s) but a redirect was '
               'issued automatically by the routing system to "%s".'
               % (request.url, exc.new_url)]

        # In case just a slash was appended we can be extra helpful
        if request.base_url + '/' == exc.new_url.split('?')[0]:
            buf.append('  The URL was defined with a trailing slash so '
                       'Flask will automatically redirect to the URL '
                       'with the trailing slash if it was accessed '
                       'without one.')

        buf.append('  Make sure to directly send your %s-request to this URL '
                   'since we can\'t make browsers or HTTP clients redirect '
                   'with form data reliably or without user interaction.' %
                   request.method)
        buf.append('\n\nNote: this exception is only raised in debug mode')
        # TODO: This is not working with py.test due to the assertion error 
        super(AssertionError, self).__init__(''.join(buf).encode('utf-8'))                                                                                                                              

class AttributeMapper(dict):
    """a dictionary like object which also is accessible via getattr/setattr"""

    __slots__ = []

    def __init__(self, default={}, *args, **kwargs):
        super(AttributeMapper, self).__init__(*args, **kwargs)
        self.update(default)
        self.update(kwargs)

    def __getattr__(self, k):
        """retrieve some data from the dict"""
        if self.has_key(k):
            return self[k]
        raise AttributeError(k)

    def __setattr__(self, k,v):
        """store an attribute in the map"""
        self[k] = v

    def _clone(self):
        """return a clone of this object"""
        d = copy.deepcopy(self) 
        return AttributeMapper(d)

    def update(self, d):
        """update the dictionary but make sure that existing included AttributeMappers are only updated aswell"""
        for a,v in d.items():
            if a not in self:
                self[a] = v
            elif isinstance(self[a], AttributeMapper) and type(v) == types.DictType:
                self[a].update(v)
            elif type(self[a]) == types.DictType and type(v) == types.DictType:
                self[a].update(v)
            else:
                self[a] = v


class URL(object):
    """proxy object for a URL rule in order to be used more easily in route listings"""

    def __init__(self, path, endpoint = None, handler = None, **options):
        """initialize the route url basically with what we need for werkzeug routes"""
        self.path = path
        self.endpoint = endpoint
        self.handler = handler
        self.options = options

