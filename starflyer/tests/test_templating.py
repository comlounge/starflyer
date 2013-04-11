
def test_templating(client):
    resp = client.get("/render")
    assert resp.data == "<h1>rendered</h1>" 

def test_templating_vars(client):
    resp = client.get("/render?content=foobar")
    assert resp.data == "<h1>foobar</h1>" 

def test_render_context(client):
    resp = client.get("/render?tmpl=index2.html")
    assert resp.data == "<h1>from context</h1>" 

def test_render_context_override(client):
    resp = client.get("/render?tmpl=index3.html")
    assert resp.data == "<h1>stuff from call</h1>" 


