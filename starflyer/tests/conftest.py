from starflyer import Handler, Application, AttributeMapper, URL, redirect, Module
from starflyer import exceptions
import werkzeug
import starflyer
import pytest
import pkg_resources

class MyErrorHandler(Handler):
    
    def get(self, exception=None):
        return "my custom error handler"

class BrokenHandler(Handler):

    def get(self):
        # call something which leads to an error
        return broken()

class FlashHandler(Handler):

    def get(self):
        params = self.request.args
        if "flash" in params:
            self.flash(params['flash'])
            return "ok"
        else:
            return str(self.get_flashes())

class RenderHandler(Handler):
    """for template testing"""

    template = "index.html"

    @property
    def render_context(self):
        return dict(new_content = "from context", stuff="stuff from context")

    def get(self):
        params = self.request.args
        if "tmpl" in params:
            tmplname = params['tmpl']
            return self.render(tmplname, stuff="stuff from call")
        content = "rendered"
        if "content" in params:
            content = params['content']
        return self.render(content=content, stuff="stuff from call")

class TestHandler1(Handler):

    def get(self):
        return "test1"

    def before(self):
        self.test_before = "foobar" # remember something in handler

    def after(self, response):
        # consume the remembered item and put it into headers
        response.headers['X-After'] = self.test_before

        # this is for testing the modules defined below which set ``handler.foobar``
        foobar = getattr(self, "foobar", "")
        response.headers['X-Module'] = foobar
        return response

class TestHandler2(Handler):

    def get(self):
        return "test2"

class TestHandler3(Handler):

    def get(self, id=''):
        return str(id)

class RedirectHandler(Handler):
    """test handler for redirects"""

    def get(self):
        return redirect(self.url_for("huhu"))

class SessionHandler(Handler):
    """test handler for session testing"""

    def get(self):
        params = self.request.args
        self.session['foo'] = params.get("s", "bar")
        if "permanent" in params:
            self.session.permanent = True
        return "ok"

class CheckSessionHandler(Handler):
    """test handler for session testing"""

    def get(self):
        return self.session['foo']
    
class TestApplication(Application):

    error_handlers = {
        500: MyErrorHandler,
    }

    routes = [
        URL("/",            "index",        TestHandler1),
        URL("/huhu",        "huhu",         TestHandler2),
        URL("/render",      "render",       RenderHandler),
        URL("/post/<id>",   "post",         TestHandler3),
        URL("/redirect",    "redirect",     RedirectHandler),
        URL("/session",     "session",      SessionHandler),
        URL("/check_session",     "check_session",      CheckSessionHandler),
        URL("/flash",     "flash",          FlashHandler),
        URL("/branch/",     "branch",       FlashHandler),
        URL("/broken",     "broken",       BrokenHandler),
    ]

    defaults = {
        'template_folder'       : 'test_templates/',
        'debug'                 : False,
        'testing'               : True,
        'session_cookie_domain' : '',
        'server_name'           : '',
    }

    first_counter = 0

    def before_first_request(self, request):
        self.first_counter = self.first_counter + 1

    def finalize_response(self, response):
        if not isinstance(response, werkzeug.exceptions.HTTPException):
            response.headers['X-Finalize'] = 1
        return response
        

def pytest_funcarg__app(request):
    return TestApplication(__name__)

def pytest_funcarg__session_handler(request):
    app = request.getfuncargvalue('app')
    app.config.testing = False
    request = starflyer.Request({})
    return SessionHandler(app, request)
    
def pytest_funcarg__client(request):
    app = request.getfuncargvalue('app')
    return werkzeug.Client(app, werkzeug.BaseResponse)

class TestModule1(Module):
    """test module"""
    name = "testmodule1"

    defaults = {
        'testvar' : 'foobar'
    }

    def before_handler(self, handler):
        """set something on the handler for testing"""
        handler.foobar = self.config.testvar

test_module = TestModule1(__name__)

class ModuleTestApplication1(Application):
    """app for testing the base module functionality"""

    routes = [
        URL("/",            "index",        TestHandler1),
    ]

    modules = [
        test_module(),
    ]

    defaults = {
        'template_folder'   : 'test_templates/',
        'debug'             : False,
        'testing'           : True,
    }

test_module = TestModule1(__name__)
class ModuleTestApplication2(ModuleTestApplication1):
    """same as above but we change the config of the module"""

    modules = [
        test_module(testvar="barfooz"),
    ]
    def finalize_setup(self):
        print "huhu?"


test_module = TestModule1(__name__)
class ModuleTestApplication3(ModuleTestApplication1):
    """same as above but we configure the module dynamically"""

    defaults = {
        'testvar' : 't3',
    }

    modules = []

    def finalize_modules(self):
        self.modules.append(test_module(testvar = self.config.testvar))

def pytest_funcarg__module_app1(request):
    return ModuleTestApplication1(__name__)

def pytest_funcarg__client_mod_app1(request):
    app = request.getfuncargvalue('module_app1')
    return werkzeug.Client(app, werkzeug.BaseResponse)

def pytest_funcarg__module_app2(request):
    return ModuleTestApplication2(__name__)

def pytest_funcarg__client_mod_app2(request):
    app = request.getfuncargvalue('module_app2')
    return werkzeug.Client(app, werkzeug.BaseResponse)

def pytest_funcarg__module_app3(request):
    return ModuleTestApplication3(__name__)

def pytest_funcarg__client_mod_app3(request):
    app = request.getfuncargvalue('module_app3')
    return werkzeug.Client(app, werkzeug.BaseResponse)

@pytest.fixture
def module_test_client1(request):
    """provides an app with a module for testing module templates and overrides"""
    from mods.testmodule import testmodule1

    class App(Application):
        """same as above but we configure the module dynamically"""

        defaults = {
            'testing' : True,
        }

        modules = [
            testmodule1()
        ]
    app = App(__name__)
    return werkzeug.Client(app, werkzeug.BaseResponse)


@pytest.fixture
def module_test_client2(request):
    """provides an app with a module for testing module templates and overrides.
    this uses a different template folder"""
    from mods.testmodule import testmodule2

    class App(Application):
        """same as above but we configure the module dynamically"""

        defaults = {
            'testing' : True,
        }

        modules = [
            testmodule2()
        ]
    fn = pkg_resources.resource_filename(__name__, 'testconfig.ini')
    app = App(__name__, {'module_config_file' : fn})
    return werkzeug.Client(app, werkzeug.BaseResponse)

