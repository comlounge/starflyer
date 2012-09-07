from starflyer import Handler, Application, AttributeMapper, URL, redirect
from starflyer import exceptions
import werkzeug
import starflyer

class MyErrorHandler(Handler):
    
    def get(self, exception=None):
        return "my custom error handler"

class BrokenHandler(Handler):

    def get(self):
        # call something which leads to an error
        print "doing something broken here"
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
        print params
        if "tmpl" in params:
            tmplname = params['tmpl']
            print tmplname
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
        'template_folder'   : 'test_templates/',
        'debug'             : False,
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
    request = starflyer.Request({})
    return SessionHandler(app, request)
    
def pytest_funcarg__client(request):
    app = request.getfuncargvalue('app')
    return werkzeug.Client(app, werkzeug.BaseResponse)





