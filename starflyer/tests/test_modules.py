def test_module_before_handler(client_mod_app1):
    resp = client_mod_app1.get('/')
    assert resp.headers['X-Module'] == 'foobar'

def test_module_before_handler_with_custom_config(client_mod_app2):
    resp = client_mod_app2.get('/')
    assert resp.headers['X-Module'] == 'barfooz'

def test_module_before_handler_with_module_finalize(client_mod_app3):
    resp = client_mod_app3.get('/')
    assert resp.headers['X-Module'] == 't3'
