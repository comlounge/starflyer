from starflyer import Application, Handler, URL
import werkzeug
import starflyer


# some subclasses to be tested
class TestRequest(starflyer.Request):
    testing = True

class TestResponse(starflyer.Response):
    testing = True

class URLRuleClass(werkzeug.routing.Rule):
    testing = True

class TestHandler(Handler):
    """in order to test these classes properly we need some handler
    which do checks on it's own"""

    def get(self):
        self.app.test_request = self.request
        return "ok"

class TestApplication(Application):
    """our test application to check configuration"""

    request_class = TestRequest
    response_class = TestResponse
    url_rule_class = URLRuleClass

    routes = [
        URL("/",    "index",    TestHandler)
    ]

    def finalize_response(self, response):
        """we also test finalize response as well here"""
        self.test_response = response
        return response


def pytest_funcarg__app(request):
    return TestApplication(__name__)

def pytest_funcarg__client(request):
    app = request.getfuncargvalue('app')
    return werkzeug.Client(app, werkzeug.BaseResponse)

def test_request_class_override(client):
    resp = client.get('/')
    assert isinstance(client.application.test_request, TestRequest)
    
def test_response_class_override(client, app):
    resp = client.get('/')
    assert isinstance(client.application.test_response, TestResponse)
    
def test_rule_class_override(app):
    rule = list(app.url_map.iter_rules())[0]
    assert isinstance(rule, URLRuleClass)

