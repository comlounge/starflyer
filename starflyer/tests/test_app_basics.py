from starflyer.app import Application
from starflyer.handler import Handler
import werkzeug


def test_app_basics(client1):

    resp = client1.get('/')
    assert resp.status=="200 OK"
    assert resp.data == "test1"
    
    resp = client1.get('/huhu')
    assert resp.status=="200 OK"
    assert resp.data == "test2"

    
def test_app_wrong_method(client1):    

    resp = client1.post('/')
    assert resp.status=="405 METHOD NOT ALLOWED"
    
def test_app_unkown_path(client1):

    resp = client1.post('/no')
    assert resp.status=="404 NOT FOUND"
    
def test_path_params(client1):

    resp = client1.get('/post/33')
    assert resp.status=="200 OK"
    assert resp.data == "33"

        
    
