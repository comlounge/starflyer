import argparse
import yaml
import wsgiref.simple_server
import pkg_resources

class WebsiteRunner(object):
    """handler for running a website"""

    def __init__(self):
        """initialize the website runner with the arg parser etc."""
        self.parser = argparse.ArgumentParser(description='run a webserver')
        self.parser.add_argument('config_file', metavar='CONFIG', type=file, nargs=1,
                   help='the config file to read')

        args = self.parser.parse_args()
        self.config = yaml.load(args.config_file[0].read())

        # read app
        group = 'starflyer_app_factory'
        entrypoint = list(pkg_resources.iter_entry_points(group=group, name="default"))[0]
        self.app = entrypoint.load()(**self.config['app'])
        
    def run(self):
        port = self.config['website']['port']
        wsgiref.simple_server.make_server('', port, self.app).serve_forever()


def run():
    """run a website"""
    w = WebsiteRunner()
    w.run()


