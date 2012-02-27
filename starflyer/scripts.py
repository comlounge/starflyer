import argparse
import yaml
import daemon
import pkg_resources
import werkzeug.serving


class ScriptBase(object):

    def __init__(self):
        """initialize the website runner with the arg parser etc."""
        self.parser = argparse.ArgumentParser(description='run a webserver')
        self.parser.add_argument('config_file', metavar='CONFIG', type=file, nargs=1,
                   help='the config file to read')
        self.parser.add_argument('-r', action="store_true", help='use reloader')
        self.parser.add_argument('-d', action="store_true", help='use debugger')
        self.parser.add_argument('-b', action="store_true", help='run in background')

        self.args = self.parser.parse_args()
        self.config = yaml.load(self.args.config_file[0].read())

        # extract the config section which consists of a python package name and the name of an entry point
        # in the group starflyer.config. If name is not given, we use default
        self.app_section = self.config['app']
        self.server_section = self.config['server']
        self.config_section = self.config['config']


        # now retrieve the setup method we need to use. This is in the app section
        # and there inside the ``setup`` key as ``package:name`` format
        setup_string = self.app_section['setup']

        # extract the application package and entry point name
        parts = setup_string.split(":")
        package = parts[0]
        if len(parts)>1:
            name = parts[1]
        else:
            name = "default"

        # get the distribution object
        dist = pkg_resources.get_distribution(package)
        setup_method = dist.load_entry_point("starflyer.config", name)

        self.config = setup_method(**self.config_section)
        self.settings = self.config.settings

class WebsiteRunner(object):
    """handler for running a website"""

    def __init__(self):
        """initialize the website runner with the arg parser etc."""
        self.parser = argparse.ArgumentParser(description='run a webserver')
        self.parser.add_argument('config_file', metavar='CONFIG', type=file, nargs=1,
                   help='the config file to read')
        self.parser.add_argument('-r', action="store_true", help='use reloader')
        self.parser.add_argument('-d', action="store_true", help='use debugger')
        self.parser.add_argument('-b', action="store_true", help='run in background')

        self.args = self.parser.parse_args()
        self.config = yaml.load(self.args.config_file[0].read())

        # extract the config section which consists of a python package name and the name of an entry point
        # in the group starflyer.config. If name is not given, we use default
        self.app_section = self.config['app']
        self.server_section = self.config['server']
        self.config_section = self.config['config']


        # now retrieve the setup method we need to use. This is in the app section
        # and there inside the ``setup`` key as ``package:name`` format
        setup_string = self.app_section['setup']

        # extract the application package and entry point name
        parts = setup_string.split(":")
        package = parts[0]
        if len(parts)>1:
            name = parts[1]
        else:
            name = "default"

        # get the distribution object
        dist = pkg_resources.get_distribution(package)
        setup_method = dist.load_entry_point("starflyer.config", name)

        self.app_config = setup_method(**self.config_section)
        self.app = self.app_config.app(self.app_config)

    def run(self):
        port = self.server_section.get('port', 8888)
        host = self.server_section.get('host', '127.0.0.1')

        app = werkzeug.wsgi.SharedDataMiddleware(self.app, self.app_config._static_map)

        if self.args.b:
            pidfile = None
            if self.server_section.has_option("main", "pidfile"):
                path = self.server_section.get("main", "pidfile")
                pidfile=lockfile.FileLock(path)
            with daemon.DaemonContext(pidfile=pidfile):                                                                                                                                          
                werkzeug.serving.run_simple(host, port, app,
                    use_reloader=self.args.r,
                    use_debugger=self.args.d)
        else:
            werkzeug.serving.run_simple('localhost', port, app, 
                use_reloader=self.args.r,
                use_debugger=self.args.d)

def run():
    """run a website"""
    w = WebsiteRunner()
    w.run()


