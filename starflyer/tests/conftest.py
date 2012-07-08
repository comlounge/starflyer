from starflyer import Handler, Application, AttributeMapper, URL, redirect
from starflyer import exceptions
import werkzeug
import starflyer


class TestHandler1(Handler):

    def get(self):
        return "test1"

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
    
class App1(Application):

    import_name = __name__

    routes = [
        URL("/",            "index",        TestHandler1),
        URL("/huhu",        "huhu",         TestHandler2),
        URL("/post/<id>",   "post",         TestHandler3),
        URL("/redirect",    "redirect",     RedirectHandler),
    ]

def pytest_funcarg__app1(request):
    return App1()
    
def pytest_funcarg__client1(request):
    app1 = request.getfuncargvalue('app1')
    return werkzeug.Client(app1, werkzeug.BaseResponse)





