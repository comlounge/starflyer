import exceptions
import copy


import static
from .helpers import AttributeMapper, URL

class Module(object):
    """a Module is used to extend an application via a third party python package."""

    name = None
    routes = []
    module_jinja_loader = None  # templates from this loader can be found at _m/<modname>/<templatename>
    jinja_loader = None         # templates from this loader will be unprefixed in the main namespace. 
    defaults = {}               # default config dictionary providing defaults

    # some defaults we always need (like in apps)
    enforced_defaults = {
        'template_folder'               : None,
        'static_folder'                 : None,
        'static_url_path'               : None,
    }

    def __init__(self, import_name, name = None, url_prefix = ""):
        """initialize the module

        :param url_prefix: prefix under which to register all the routes. Defaults to ``None`` 
            for putting everything into the main namespace
        """

        self.import_name = import_name
        if url_prefix is not None:
            url_prefix = url_prefix.rstrip("/")
        self.url_prefix = url_prefix
        if name is not None:
            self.name = name
        if self.name is None:
            raise exceptions.ConfigurationError("you need to configure a name for your module")

    def bind_to_app(self, app):
        """called by the application object when the module is bound to the application.
        From there on we can the configuration necessary

        """
        self.app = app 

        # initialize the routes under the given prefix
        for route in self.routes:
            self.add_url_rule(
                route.path,
                route.endpoint,
                route.handler,
                **route.options)

        # add static files
        if self.config.static_folder is not None:
            sup = self.config.static_url_path
            if sup.endswith("/"):
                sup = sup[:-1]  # remove any trailing slash
            if not sup.startswith("/"):
                sup = "/"+sup   # add a leading slash if missing
            self.add_url_rule(sup+ '/<path:filename>',
                              endpoint='static',
                              handler=static.StaticFileHandler)
        

        self.finalize()

    def add_url_rule(self, url_or_path, endpoint = None, handler = None, **options):
        """module local add url rule which knows about the module namespace"""
        if isinstance(url_or_path, URL):
            path = url_or_path.path
            endpoint = url_or_path.endpoint
            handler = url_or_path.handler
            options = url_or_path.options
        else:
            path = url_or_path
        ns = self.name.strip().lower()+"."
        self.app.add_url_rule(
            self.url_prefix + path,
            ns + endpoint,
            handler,
            **options)

    def get_render_context(self, handler):
        """you can return paramaters for the render context here. You get the active handler passed
        so you can inspect the app, session, request and so on. 

        For your own parameters override this method in your module.

        :param handler: The handler for which the render context is computed
        """
        return {}

    def __call__(self, url_prefix = None, config = {}, **kw):
        """reconfigure the module when being registered in the modules list
        
        :param url_prefix: the url prefix to use for this module. If it is None the default one applies
        :param config: configuration parameters which will be available in the ``config`` instance variable of the module
        :param kw: additional keyword arguments to configure it (override everything else)
        """
        if url_prefix is not None:
            self.url_prefix = url_prefix
        else:
            self.url_prefix = "/"+self.name
        self.config = AttributeMapper(self.enforced_defaults or {})
        self.config.update(self.defaults)
        self.config.update(config)
        self.config.update(kw)
        return self

    def finalize(self):
        """finalize the setup after the module has been bound to the app"""


