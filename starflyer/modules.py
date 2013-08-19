import exceptions
import pkg_resources
import copy
import urlparse
import jinja2
import os
import copy

import static
from .helpers import AttributeMapper, URL, fix_types

class Module(object):
    """a Module is used to extend an application via a third party python package."""

    name = None
    routes = []
    module_jinja_loader = None  # templates from this loader can be found at _m/<modname>/<templatename>
    jinja_loader = None         # templates from this loader will be unprefixed in the main namespace. 
    defaults = {}               # default config dictionary providing defaults

    # some defaults we always need (like in apps)
    enforced_defaults = {
        'template_folder'               : "templates",
        'static_folder'                 : "static",
        'static_url_path'               : "/static",
    }

    # here you can define which types the config parameters are supposed to be in 
    config_types = {}

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

    ####
    #### configuration related hooks you can override
    ####

    def finalize(self):
        """finalize the setup after the module has been bound to the app"""

    ####
    #### handler related hooks you can override
    ####

    def get_render_context(self, handler):
        """you can return paramaters for the render context here. You get the active handler passed
        so you can inspect the app, session, request and so on. 

        For your own parameters override this method in your module.

        :param handler: The handler for which the render context is computed
        """
        return {}

    def before_handler(self, handler):
        """This is called from the handler after the initialization has been finished. You
        can use this to e.g. further inspect the request and put some data into the handler or it's
        session

        :param handler: The handler for which the render context is computed
        """

    def after_handler(self, handler, response):
        """This hook is run after the handler processing is done but before the response is sent
        out. You can check the handler or response and maybe return your own response here. In case
        you do that this response will be used instead. If you return None then the original handler
        response will be used.
        """

    ####
    #### module mechanics
    ####

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

        # add static files. We automatically use any static/ folder and map it to the "/<modulename>/static/" url path
        # but all of this can be overridden 
        if self.config.static_folder is not None:
            path = self.config.static_folder
            fullpath = pkg_resources.resource_filename(self.import_name, path)

            # only add the static routes if the folder exists
            if os.path.exists(fullpath):
                sup = self.config.static_url_path
                if sup.endswith("/"):
                    sup = sup[:-1]  # remove any trailing slash
                if sup.startswith("/"):
                    sup = sup[1:] # remove leading slashes so that urljoin later works correctly
                self.add_url_rule(sup+ '/<path:filename>',
                                  endpoint='static',
                                  handler=static.StaticFileHandler)

        # now set the template loader
        if self.jinja_loader is None:
            self.jinja_loader = jinja2.PackageLoader(self.import_name, self.config.template_folder)


        # now we update the module config by some config related sub section from the app's config 
        # these need to be stored in the modules sub dictionary with the module names as keys.
        # e.g. if you want to configure the mail module you'd set
        # 'modules' : {'mail' : {'debug' : False}}
        if app.config.has_key("modules"):
            modcfg = app.config['modules']
            self.config.update(fix_types(modcfg.get(self.name, {}), self.config_types))

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
        if path.startswith("/"):
            path = path[1:]
        self.app.add_url_rule(
            urlparse.urljoin(self.url_prefix,path),
            ns + endpoint,
            handler,
            **options)


    def __call__(self, url_prefix = None, config = {}, **kw):
        """reconfigure the module when being registered in the modules list
        
        :param url_prefix: the url prefix to use for this module. If it is None the default one applies
        :param config: configuration parameters which will be available in the ``config`` instance variable of the module
        :param kw: additional keyword arguments to configure it (override everything else)
        """

        self = copy.copy(self) # return a copy of this module
        if url_prefix is not None:
            self.url_prefix = url_prefix
        else:
            self.url_prefix = "/"+self.name
        if not self.url_prefix.endswith("/"):
            self.url_prefix = self.url_prefix + "/"
        self.config = AttributeMapper(self.enforced_defaults or {})
        self.config.update(copy.deepcopy(self.defaults))
        self.config.update(config)
        self.config.update(kw)
        return self



