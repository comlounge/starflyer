======================
Running an application
======================

In order to run an application you first need to create it. You mainly do this
by providing a configuration object like this::

    class MyConfiguration(starflyer.Configuration):
        """special configurator instance for usermanager with defaults"""
        defaults = {
            'cookie_secret' : "czcds7z878cdsgsdhcdjsbhccscsc87csds76876ds",
        }

        def setup_urls(self):
            """setup the url mapper"""
            self.add_rule('/', 'index', WelcomeView)

Creating a WSGI application manually
====================================

One way to run it is to create the WSGI application manually::


Another way is to simply create an entry point in your package specifying the 
main configuration object to use::

    [starflyer_configurator]
    default = 

Then you have to create an .ini file to specify the WSGI environment like this::

    [DEFAULT]                                                                                                                                             

    [app:main]
    use = egg:starflyer
    config = egg:mypackage
    ini_filename = %(here)s/../etc/${ini_filename}
    configurators = 
        egg:theme1
        egg:plugin1

    [server:main]
    use = egg:PasteScript#cherrypy
    host = 0.0.0.0
    port = 8888
    numthreads = 10



        group = 'starflyer_app_factory'
        entrypoint = list(pkg_resources.iter_entry_points(group=group, name="default"))[0]
        self.app = entrypoint.load()(**self.config['app'])




The next thing you need to do is to specify the configuration to use as an entry point::
