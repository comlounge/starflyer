import pytest

def test_route_not_found(client):
    resp = client.get("/notfound")
    assert resp.status_code == 404

def test_broken_handler_with_debug(client):
    client.application.config.debug = True
    client.application.config.testing = False # somewhat more real here
    # propagate_exception is True and thus we get the exception directly
    # which is useful in unit tests like this one
    pytest.raises(NameError, client.get, "/broken")

def test_broken_handler_no_propagate(client):
    """check if the right thing happens if we don't have an error handler defined"""
    client.application.config.debug = True
    client.application.config.testing = False # somewhat more real here
    client.application.error_handlers = {}
    # this means to use the default error handler (InternalServerError)
    client.application.config.propagate_exceptions = False
    resp = client.get("/broken")
    assert resp.status_code == 500

def test_broken_handler_propagate(client):
    """check if the right thing happens if we don't have an error handler defined"""
    client.application.config.debug = True
    client.application.config.testing = False # somewhat more real here
    client.application.error_handlers = {}
    client.application.config.propagate_exceptions = True
    pytest.raises(NameError, client.get, "/broken")

def test_error_handler(client):
    client.application.config.debug = False
    client.application.config.testing = False # somewhat more real here
    resp = client.get("/broken")
    assert resp.status_code == 200

# TODO: We need some test for some error handlers and some example

def test_strict_slashes_in_debug(client):
    client.application.config.debug = False
    client.application.config.testing = False # somewhat more real here
    resp = client.post("/branch")
    assert resp.status_code == 301
    assert resp.headers['location'] == "http://localhost/branch/"

def test_strict_slashes_no_debug(client):
    client.application.config.debug = False
    client.application.config.testing = False # somewhat more real here
    # actually you should not post to that in the first place
    resp = client.post("/branch")
    assert resp.status_code == 301
    assert resp.headers['location'] == "http://localhost/branch/"


