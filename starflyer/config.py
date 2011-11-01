from starflyer import AttributeMapper, Application
from werkzeug.routing import Map, Rule, NotFound, Submount, RequestRedirect
from logbook import Logger, FileHandler, NestedSetup, Processor

__all__ = ['Configuration']

class Mapper(object):
    """a mapper which is able to map url routes to handlers"""

    def __init__(self):
        self.url_map = Map()
        self.views = {}

    def add(self, path, endpoint, handler):
        self.url_map.add(Rule(path, endpoint=endpoint))
        self.views[endpoint] = handler

    def map(self, environ):
        """maps an environment to a handler. Returns the handler object
        and the args. If it does not match, ``(None, None)`` is returned.
        """
        urls = self.url_map.bind_to_environ(environ)
        endpoint, args = urls.match()
        return self.views.get(endpoint, None), args

    def generator(self, environ):
        return self.url_map.bind_to_environ(environ)

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
        self.templates = AttributeMapper()
        self.settings = AttributeMapper()

        # initialize default logging which might be overridden by ``register_logger()``
        self.register_default_log_handler()

        # initialize maps
        self._static_map = {}
        self._url_map = Mapper()

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

    def register_paths(self, *paths):
        """register url paths
        
        :param paths: A list of tuples consisting of ``path``, ``endpoint`` and ``handler`` to be registered
            with ``register_path()``
        """
        for path, endpoint, handler in paths:
            self.register_path(path, endpoint, handler)

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

    def register_path(self, path, endpoint, handler):
        """add a rule to the view mapper"""
        self._url_map.add(path, endpoint, handler)

    def register_default_log_handler(self):
        """register the default logger in case nothing else is registered """
        #handler = FileHandler(self.settings.log_filename, bubble=True)
        self.log_handler = NestedSetup([
            #handler,
        ])



