import pytest

def test_route_not_found(client):
    resp = client.get("/notfound")
    assert resp.status_code == 404

def test_broken_handler_with_debug(client):
    client.application.config.debug = True
    # propagate_exception is True and thus we get the exception directly
    # which is useful in unit tests like this one
    pytest.raises(NameError, client.get, "/broken")

def test_broken_handler_no_propagate(client):
    client.application.config.debug = True
    client.application.config.propagate_exceptions = False
    resp = client.get("/broken")
    assert resp.status_code == 500

def test_error_handler(client):
    client.application.config.debug = False
    resp = client.get("/broken")
    assert resp.status_code == 500
    assert resp.data == "my custom error handler"

    # TODO: Error handlers need some overhaul! We do not need methods and they are not supposed to return
    # 200 status codes. They probably simply need a process() method. They also need to be able to get the
    # status code passed in.

# TODO: This uses an AssertionError internally which fails as it's also patched by pytest
@pytest.mark.xfail()
def test_strict_slashes_in_debug(client):
    client.application.config.debug = True
    resp = client.post("/branch")
    assert resp.status_code == 301
    assert resp.headers['location'] == "http://localhost/branch/"

def test_strict_slashes_no_debug(client):
    client.application.config.debug = False
    # actually you should not post to that in the first place
    resp = client.post("/branch")
    assert resp.status_code == 301
    assert resp.headers['location'] == "http://localhost/branch/"


