from starflyer import Module, Handler, URL

class Handler1(Handler):

    template = "test.html"

    def get(self):
        return self.render()

class Handler2(Handler1):

    template = "test2.html" # exists in the module and the app

class TestModule1(Module):
    """this is a test module"""

    name = "test"

    routes = [
        URL("/",            "index",        Handler1),
        URL("/override",    "override",     Handler2),
    ]

testmodule1 = TestModule1(__name__)

class TestModule2(Module):
    """this is a test module using a different template folder"""

    name = "test"
    defaults = {
        'template_folder' : 'templates2',
    }

    routes = [
        URL("/",            "index",        Handler1),
    ]

testmodule2 = TestModule2(__name__)
