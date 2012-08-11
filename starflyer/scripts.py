import argparse
import os
from paste.deploy import loadapp



class ScriptBase(object):

    description = "a script"

    def __init__(self):
        """initialize the website runner with the arg parser etc."""
        self.parser = argparse.ArgumentParser(description=self.description)
        self.parser.add_argument('-f', dest="config_file", metavar='CONFIG', nargs=1, help='the paster config file to read') 
        self.extend_parser()

        self.args = self.parser.parse_args()
        path = self.args.config_file[0]
        relative_to = os.getcwd()
        self.app = loadapp("config:"+path, relative_to = relative_to)

    def extend_parser(self):
        """hook for extending the parser by adding new parameters"""



