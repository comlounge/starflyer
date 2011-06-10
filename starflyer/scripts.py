import argparse
import yaml
import pkg_resources
import werkzeug.serving

class WebsiteRunner(object):
    """handler for running a website"""

    def __init__(self):
        """initialize the website runner with the arg parser etc."""
        self.parser = argparse.ArgumentParser(description='run a webserver')
        self.parser.add_argument('config_file', metavar='CONFIG', type=file, nargs=1,
                   help='the config file to read')
        self.parser.add_argument('-r', action="store_true", help='use reloader')
        self.parser.add_argument('-d', action="store_true", help='use debugger')

        self.args = self.parser.parse_args()
        self.config = yaml.load(self.args.config_file[0].read())

        # read app
        group = 'starflyer_app_factory'
        entrypoint = list(pkg_resources.iter_entry_points(group=group, name="default"))[0]
        self.app = entrypoint.load()(**self.config['app'])
        
    def run(self):
        port = self.config['website']['port']
        werkzeug.serving.run_simple('localhost', port, self.app, 
            use_reloader=self.args.r,
            use_debugger=self.args.d)

class ScriptBase(object):
    """handler for running a script under a certain context. Simply
    derive from this class and add a ``__call__()`` method."""

    description = "run a dummy script"

    def __init__(self):
        """initialize the script runner with the arg parser etc."""
        self.parser = argparse.ArgumentParser(description=self.description)
        self.parser.add_argument('config_file', metavar='CONFIG', type=file, nargs=1,
                   help='the config file to use for this script')

        self.args = self.parser.parse_args()
        self.config = yaml.load(self.args.config_file[0].read())

        # read app
        group = 'starflyer_setup'
        entrypoint = list(pkg_resources.iter_entry_points(group=group, name="default"))[0]
        self.settings = entrypoint.load()(**self.config['app'])
        
    def __call__(self): 
        print "please override this method to run a script within settings %s " %self.settings

def run():
    """run a website"""
    w = WebsiteRunner()
    w.run()


