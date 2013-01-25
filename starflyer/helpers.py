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
            # test for sub dictionary updates like ``mail.module.debug``
            if "." in a:
                prefix, remainder = a.split(".", 1)

                # if prefix is not in this main dict, then we simply ignore if for now. 
                if prefix not in self:
                    raise ValueError("WARNING: %s does not exist! (from %s)" %(prefix,a))

                # if it is in the existing dictionary, then we check if the value is an AttributeMapper as well
                # only AttributeMappers will be recursively updated 
                # TODO: Add some flag to convert dicts to AMs on the fly
                if isinstance(self[prefix], AttributeMapper):
                    self[prefix].update({remainder: v})
                    continue
                else:
                    # we cannot update anything here as it's not a dict so we discard it
                    # existing default config type always wins!
                    raise ValueError("WARNING: tried to update %s but %s is not an AttributeMapper!" %(prefix, self[prefix]))

            if a not in self:
                self[a] = v
            elif isinstance(self[a], AttributeMapper) and type(v) == types.DictType:
                # this might be recursive
                self[a].update(v)
            elif type(self[a]) == types.DictType and type(v) == types.DictType:
                # this ain't recursive as dictionaries don't updata that way
                self[a].update(v)
            else:
                self[a] = v


class URL(object):
    """proxy object for a URL rule in order to be used more easily in route listings"""

    def __init__(self, path, endpoint = None, handler = None, **options):
        """initialize the route url basically with what we need for werkzeug routes

        :param path: the rule string which is passed to the werkzeug Rule as first parameter
        :param endpoint: the endpoint name under which a rule can be referenced again
        :param handler: the starflyer ``Handler`` to be used for this rule
        :param options: further options which are passed into the werkzeug ``Rule``
        """
        self.path = path
        self.endpoint = endpoint
        self.handler = handler
        self.options = options

def fix_types(params, type_map):
    """fixes parameters which might come in as string but need to be e.g. boolean

    :param params: A dictionary with configuration parameters
    :param type_map: A dictionary mapping parameter keys to types such as bool

    If a key is not present in the type map then it will simply be passed as it is.

    Right now this method supports ``bool`` and ``int``
    
    """

    new_config = {}
    for a,v in params.items():
        if a not in type_map:
            new_config[a] = v
            continue
        if type_map[a] == bool:
            if type(v)==types.BooleanType:
                new_config[a] = v
            else:
                new_config[a] = v.lower()=="true"
        elif type_map[a] == int:
            new_config[a] = int(v)
    return new_config


    
