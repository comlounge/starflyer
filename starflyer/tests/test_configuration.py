from starflyer import Application
from starflyer.static import StaticFileHandler
import werkzeug
import starflyer
from werkzeug.test import EnvironBuilder
from StringIO import StringIO


class TestApplication(Application):
    """our test application to check configuration"""

    template_folder = "test_templates/"
    static_folder = "static_folder/"
    static_url_path = "/assets/"

    import_name = __name__

    defaults = {
        'debug'             : True, 
        'title'             : "foobar",
        'description'       : "barfoo",
    }

def pytest_funcarg__app(request):
    return TestApplication()

def test_template_folder_override(app):
    assert app.template_folder == "test_templates/"
    tmpl = app.jinja_env.get_or_select_template("foobar.html")
    assert tmpl.render() == "TEST"

def test_static_folder_override(app):
    assert app.static_folder == "static_folder/"
    request = starflyer.Request({})
    handler = StaticFileHandler(app, request)
    response = handler.get(filename="test.txt")
    assert response.data == "TEST\n"

def test_static_url_path_override(app):
    assert app.static_url_path == "/assets/"
    builder = EnvironBuilder(method='GET', path="/assets/test.txt")
    env = builder.get_environ()
    request = starflyer.Request(env)
    response = app.process_request(request)
    assert response.data == "TEST\n"


    
    


"""
- check different url rule class
- check different response class
- check different request class
- check different session interface
- check enforced defaults
- check jinja options
- check first request
- check finalize response


"""
