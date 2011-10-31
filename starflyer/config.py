from starflyer import AttributeMapper

__all__ = ['Configuration']

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
    sections = []
    defaults = {}

    def __init__(self, *args, **kwargs):
        """initialize the configuration with an optional dictionary containing
        values to override the default values"""
        super(AttributeMapper, self).__init__(*args, **kwargs)
        self.templates = AttributeMapper()
        for name in self.sections:
            self[name] = AttributeMapper()
        self.settings = AttributeMapper(self.defaults)
        self._static_map = {}

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



