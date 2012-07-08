from starflyer import Handler, Application, AttributeMapper
from starflyer import asjson
from starflyer import exceptions
import werkzeug


class TestHandler1(Handler):
    def get(self):
        return werkzeug.Response("test1")

class TestHandler2(Handler):
    def get(self):
        return werkzeug.Response("test2")

class TestHandler3(Handler):
    def get(self, id=''):
        return werkzeug.Response(str(id))

class RedirectHandler(Handler):
    """test handler for redirects"""
    def get(self):
        url = "/huhu"
        redirect = exceptions.Redirect(location=url)
        raise redirect
    

    
class App1(Application):

    def setup_handlers(self, map):
        map.connect(None, "/", handler=TestHandler1)
        map.connect(None, "/huhu", handler=TestHandler2)
        map.connect(None, "/post/{id}", handler=TestHandler3)
        map.connect(None, "/redirect", handler=RedirectHandler)

def pytest_funcarg__settings(request):
    td = request.getfuncargvalue('tmpdir')
    return AttributeMapper({
        'log_filename' : str(td.join("log")),
        'log_name' : "test",
        'foo' : 'bar'
    })


def pytest_funcarg__app1(request):
    settings = request.getfuncargvalue('settings')
    return App1(settings)
    
def pytest_funcarg__client1(request):
    app1 = request.getfuncargvalue('app1')
    return werkzeug.Client(app1, werkzeug.BaseResponse)





