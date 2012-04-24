from starflyer import AttributeMapper, Application
from events import Events
from werkzeug.routing import Map, Rule, NotFound, Submount, RequestRedirect
from logbook import Logger, FileHandler, NestedSetup, Processor
import jinja2
import urlparse

__all__ = ['Configuration']


class SnippetChain(list):
    """a list of snippets but with the possibility to render it"""

    def __call__(self, *args, **kwargs):
        """call all snippet chain. This will call all the snippet providers with the given arguments.
        The application must define for itself which parameters are passed for which chain.
        """
        out = []
        for provider in self:
            out.append(provider(*args, **kwargs))
        return "\n".join(out)

class Routes(list):
    """a list of routes which will be postprocessed later to create a routing map.

    In phase one we will only collect routes as 3-tuples though.

    Each tuple consists of:

    :param path: the url pattern which matches the path. See werkzeug docs for how to construct it.
    :param endpoint: a unique name for this rule which can be used later again to construct a URL
    :param handler: The handler class to be used if this path matches

    """

    def create_map(self, virtual_path=None, subdomain = None, vhost = None):
        """create a map from the stored routes taking an optional virtual path in account"""

        # rulify the routes
        rules = []
        views = {}
        for path, endpoint, handler in self:
            rules.append(Rule(path, endpoint=endpoint))
            views[endpoint] = handler

        if vhost is not None:
            virtual_path = vhost.path

        # now eventually prefix the map if a virtual path is given
        if virtual_path is not None:
            map = Map([Submount(virtual_path, rules)])
        else:
            map = Map(rules)
        return Mapper(map, views, subdomain = subdomain, vhost = vhost)

class Mapper(object):
    """a mapper which is able to map url routes to handlers"""

    def __init__(self, map, views, subdomain = None, vhost = None):
        """initialize the Mapper object with a URL map and a views dictionary

        Optionally you can pass in a ``server_name`` or ``subdomain`` which will 
        be used in URL generation. Check the werkzeug ``bind_to_environ()`` documentation
        on how it is used"""

        self.url_map = map
        self.views = views
        self.subdomain = subdomain
        self.vhost = vhost

    def add(self, path, endpoint, handler):
        self.url_map.add(Rule(path, endpoint=endpoint))
        self.views[endpoint] = handler

    def map(self, environ):
        """maps an environment to a handler. Returns the handler object
        and the args. If it does not match, ``(None, None)`` is returned.
        """
        if self.vhost is None:
            urls = self.url_map.bind_to_environ(environ)
        else:
            scheme = self.vhost.scheme
            server_name = self.vhost.netloc
            urls = self.url_map.bind(server_name, environ.get('SCRIPT_NAME'),
                        self.subdomain, scheme,
                        environ['REQUEST_METHOD'], environ.get('PATH_INFO'),
                        query_args=environ.get('QUERY_STRING', ''))
        endpoint, args = urls.match()
        return self.views.get(endpoint, None), args

    def generator(self, environ):
        if self.vhost is None:
            return self.url_map.bind_to_environ(environ, subdomain = self.subdomain)
        else:
            scheme = self.vhost.scheme
            server_name = self.vhost.netloc
            return self.url_map.bind(server_name, environ.get('SCRIPT_NAME'),
                        self.subdomain, scheme,
                        environ['REQUEST_METHOD'], environ.get('PATH_INFO'),
                        query_args=environ.get('QUERY_STRING', ''))

    def add_submapper(self, submapper):
        """attach a submapper to us"""
        self.url_map.add(submapper.url_map)
        self.views.update(submapper.views)

class Submapper(object):
    """a mapper for sub modules which mainly delegates"""

    def __init__(self, path):
        self.url_map = Submount(path, [])
        self.views = {}

    def add(self, path, endpoint, handler):
        self.add_rule(Rule(path, endpoint=endpoint))
        self.add_view(endpoint, handler)

    def add_rule(self, rule):
        """add a Rule instance to the map"""
        self.url_map.rules.append(rule)

    def add_view(self, endpoint, handler):
        """add a mapping between one endpoint and a handler"""
        self.views[endpoint] = handler

class Configuration(AttributeMapper):
    """ 
    a class holding the app wide configuration. This includes both runtime
    configuration but also component setup such as templates, static files,
    database classes and more.

    The `Configuration` object is divided into multiple parts holding
    configuring separate aspects of the application. 

    You can also configure an entry point in your own application ini file to
    override the complete configuration of an application.

    This configuration instance is then passed into the application object to
    configure it. Moreover it is passed along to all handlers and components
    used by the application.

    """
    app = Application

    def __init__(self, *args, **kwargs):
        """initialize the configuration with an optional dictionary containing
        values to override the default values"""
        super(AttributeMapper, self).__init__(*args, **kwargs)

        # create predefined sections
        self.templates = AttributeMapper() # a mapping of names to template loader chains
        self.events = Events() # a mapping from event names to a list of event handlers
        self.settings = AttributeMapper() # generic settings attributes
        self.routes = Routes() # basically a list of routing tuples
        self.snippets = AttributeMapper() # holds snippets to be used in templates. Each entry is a list mapping from a snippet name to a list of snippets

        # initialize default logging which might be overridden by ``register_logger()``
        self.register_default_log_handler()

        # initialize maps
        self._static_map = {}

    def register_snippet_names(self, *names):
        """register a list of names for snippets which can be used in templates later on"""
        for name in names:
            self.snippets[name] = SnippetChain()

    def register_template_chains(self, *chains):
        """register different template loader chains. Each template chain can be
        modified by plugins and can be used for different purposes, e.g. one chain
        for web user, one for email use.

        After initializing the chains you can then simply add loaders to them, e.g.

        config.register_template_chains("main")
        config.templates.main.append(FileSystemLoader('/path/to/user/templates'))

        :param chains: A list of names of template chains
        """
        for chain in chains:
            self.templates[chain] = []

    def register_sections(self, *sections):
        """extend the configuration object by adding new sections to structure configuration more.
        Each section will be initialized as an empty ``AttributeMapper`` instance.
        
        :param sections: A list of names of sections to be created
        """
        for name in sections:
            self[name] = AttributeMapper()

    def update_settings(self, data):
        """update the runtime configuration section.

        :param data: a dictionary passed in to overwrite certain fields in the settings section
        """
        self.settings.update(data)

    def register_static_path(self, url_path, file_path):
        """register a static file path to be used for serving static file via a middleware.
        When extending a configuration you can add your own paths here which then will be setup
        by the application

        :param url_path: The URL path to the resource, e.g. ``/css``
        :param file_path: The corresponding filesystem path, e.g. ``/home/user/static/css``
            Usually you will generate it though like this::
                static_file_path =  pkg_resources.resource_filename(__name__, 'static')
                file_path = os.path.join(static_file_path, 'css')
        """
        self._static_map[url_path] = file_path

    def register_default_log_handler(self):
        """register the default logger in case nothing else is registered """
        #handler = FileHandler(self.settings.log_filename, bubble=True)
        self.log_handler = NestedSetup([
            #handler,
        ])

    def finalize(self):
        """finalize the configuration object. This method is called after all 
        plugins have been able to modify the config. Here we then finalize template
        loaders etc.
        """

        # fixup templates
        for name, chain in self.templates.items():
            self.templates[name] = jinja2.Environment(loader = jinja2.ChoiceLoader(chain))
        
        # virtual host can define schema, host and also path
        virtual_host = self.settings.get("virtual_host", None)
        vhost = None
        if virtual_host is not None:
            vhost = urlparse.urlparse(virtual_host) # a vhost is the result of an url parse call

        subdomain = self.settings.get("subdomain", None)
        vpath = self.settings.get("virtual_path", "/" )
        self._url_map = self.routes.create_map(virtual_path = vpath, subdomain = subdomain, vhost = vhost)

        # call the finalize handlers
        self.events.handle("starflyer.config.finalize:after", self)





