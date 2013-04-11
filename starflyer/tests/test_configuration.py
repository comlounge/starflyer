from starflyer import Application
from starflyer.static import StaticFileHandler
import werkzeug
import starflyer
from werkzeug.test import EnvironBuilder
from StringIO import StringIO


class TestApplication(Application):
    """our test application to check configuration"""

    defaults = {
        'debug'                 : True, 
        'title'                 : "foobar",
        'description'           : "barfoo",
        'preferred_url_scheme'  : "https",
        'template_folder'       : 'test_templates/',
        'static_folder'         : 'static_folder/',
        'static_url_path'       : '/assets/',
    }

    def finalize_setup(self):
        self.config.description = "barfoo2"

def pytest_funcarg__app(request):
    return TestApplication(__name__)

def test_template_folder_override(app):
    assert app.config.template_folder == "test_templates/"
    tmpl = app.jinja_env.get_or_select_template("foobar.html")
    assert tmpl.render() == "TEST"

def test_static_folder_override(app):
    assert app.config.static_folder == "static_folder/"
    request = starflyer.Request({})
    handler = StaticFileHandler(app, request)
    response = handler.get(filename="test.txt")
    assert response.data == "TEST\n"

def test_static_url_path_override(app):
    assert app.config.static_url_path == "/assets/"
    builder = EnvironBuilder(method='GET', path="/assets/test.txt")
    env = builder.get_environ()
    request = starflyer.Request(env)
    response = app.process_request(request)
    assert response.data == "TEST\n"

def test_jinja_options_override(app):
    app.jinja_options = dict(app.jinja_options)
    app.jinja_options['cache_size'] = 100 # just for checking
    assert app.jinja_env.cache.capacity == 100
    
def test_jinja_environment_is_cached(app):
    assert app.jinja_env.cache.capacity == 50
    app.jinja_options = dict(app.jinja_options)
    app.jinja_options['cache_size'] = 100 # just for checking
    assert app.jinja_env.cache.capacity == 50

def test_defaults(app):
    assert app.config.title == "foobar"

def test_config_override(app):
    assert app.config.description == "barfoo2"

def test_enforced_defaults(app):
    assert app.config.session_cookie_name == "s"

def test_enforced_defaults_override(app):
    assert app.config.preferred_url_scheme == "https"



"""
- check different session interface


"""
