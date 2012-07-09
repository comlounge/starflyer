
def test_app_basics(client):

    resp = client.get('/')
    assert resp.status=="200 OK"
    assert resp.data == "test1"
    
    resp = client.get('/huhu')
    assert resp.status=="200 OK"
    assert resp.data == "test2"

    
def test_app_wrong_method(client):    

    resp = client.post('/')
    assert resp.status=="405 METHOD NOT ALLOWED"
    
def test_app_unkown_path(client):

    resp = client.post('/no')
    assert resp.status=="404 NOT FOUND"
    
def test_path_params(client):

    resp = client.get('/post/33')
    assert resp.status=="200 OK"
    assert resp.data == "33"

        
def test_redirect(client):

    resp = client.get('/redirect', follow_redirects = True)
    assert resp.status=="200 OK"
    assert resp.data == "test2"

def test_strict_slashes(client):
    resp = client.post("/branch")
    assert resp.status_code == 301
    assert resp.headers['location'] == "http://localhost/branch/"

    resp = client.get("/branch/")
    assert resp.status_code == 200
