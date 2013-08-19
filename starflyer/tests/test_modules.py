def test_module_before_handler(client_mod_app1):
    resp = client_mod_app1.get('/')
    assert resp.headers['X-Module'] == 'foobar'

def test_module_before_handler_with_custom_config(client_mod_app2):
    resp = client_mod_app2.get('/')
    assert resp.headers['X-Module'] == 'barfooz'

def test_module_before_handler_with_module_finalize(client_mod_app3):
    resp = client_mod_app3.get('/')
    assert resp.headers['X-Module'] == 't3'

def test_module_template_without_override(module_test_client1):
    resp = module_test_client1.get('/test/')
    assert resp.data == "test1"
    
def test_module_template_with_override(module_test_client1):
    resp = module_test_client1.get('/test/override')
    assert resp.data == "app"
    
def test_module_with_different_template_folder(module_test_client2):
    resp = module_test_client2.get('/test/')
    assert resp.data == "other template folder"

def test_static_files(module_test_client1):
    resp = module_test_client1.get('/test/static/moduletest.txt')
    assert resp.data.strip() == "module static file"

def test_static_files_with_different_folder_and_url_path(module_test_client2):
    resp = module_test_client2.get('/test/newstatic/moduletest.txt')
    assert resp.data.strip() == "new module static file"

def test_module_config_defaults(module_test_client1):
    resp = module_test_client1.get('/test/config')
    assert resp.data.strip() == "foo"

def test_module_config_external(module_test_client2):
    resp = module_test_client2.get('/test/config')
    assert resp.data.strip() == "bar"


