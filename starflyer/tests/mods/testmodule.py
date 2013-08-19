from starflyer import Module, Handler, URL

class Handler1(Handler):

    template = "test.html"

    def get(self):
        return self.render()

class Handler2(Handler1):

    template = "test2.html" # exists in the module and the app

class ConfigHandler(Handler):
    
    def get(self):
        """return a config variable from the module"""
        return self.module.config.test


class TestModule1(Module):
    """this is a test module"""

    name = "test"

    defaults = {
        'test' : 'foo',
    }

    routes = [
        URL("/",            "index",        Handler1),
        URL("/override",    "override",     Handler2),
        URL("/config",      "config",       ConfigHandler),
    ]

testmodule1 = TestModule1(__name__)

class TestModule2(Module):
    """this is a test module using a different template folder"""

    name = "test"

    defaults = {
        'template_folder'   : 'templates2',
        'static_folder'     : 'static2',
        'static_url_path'   : 'newstatic',
        'test'              : 'foo',
    }

    routes = [
        URL("/",            "index",        Handler1),
        URL("/config",      "config",       ConfigHandler),
    ]

testmodule2 = TestModule2(__name__)
