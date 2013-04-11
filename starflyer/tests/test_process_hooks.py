
def test_finalize_response(client):
    resp = client.get('/redirect', follow_redirects = True)
    assert resp.headers['X-Finalize'] == '1'

def test_first_request(client):
    app = client.application
    assert app.first_counter == 0 
    resp = client.get('/')
    assert app.first_counter == 1 
    resp = client.get('/')
    assert app.first_counter == 1 

def test_before_and_after(client):
    resp = client.get('/')
    assert resp.headers['X-After'] == 'foobar'

