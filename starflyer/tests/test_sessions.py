import pytest
from conftest import SessionHandler
import re
import datetime
from werkzeug.http import parse_date

def test_missing_session(session_handler):
    """test a session"""
    pytest.raises(RuntimeError, session_handler.get )

def test_session_set(app):
    """test a session"""
    app.config.secret_key = "foobar"
    response = app.run_request(path="/session")
    assert "Set-Cookie" in response.headers
    assert response.headers['Set-Cookie'].startswith("s=")

def test_session_set_and_get(client):
    """test a session"""
    client.application.config.secret_key = "foobar"
    resp = client.get("/session")
    resp = client.get("/check_session")
    assert resp.data == "bar"

def test_session_modify(client):
    """test a session modification"""
    client.application.config.secret_key = "foobar"
    resp = client.get("/session")
    resp = client.get("/session?s=new")
    resp = client.get("/check_session")
    assert resp.data == "new"

def test_session_permanent(client):
    """test a session expiration"""
    client.application.config.secret_key = "foobar"
    resp = client.get("/session?permanent=1")
    assert 'set-cookie' in resp.headers
    match = re.search(r'\bexpires=([^;]+)', resp.headers['set-cookie'])
    expires = parse_date(match.group())
    expected = datetime.datetime.utcnow() + client.application.config.permanent_session_lifetime
    assert expires.year == expected.year
    assert expires.month == expected.month
    assert expires.day == expected.day

    
def test_session_nonpermanent(client):
    """test a session expiration"""
    client.application.config.secret_key = "foobar"
    resp = client.get("/session")
    assert 'set-cookie' in resp.headers
    match = re.search(r'\bexpires=([^;]+)', resp.headers['set-cookie'])
    assert match is None

def test_session_config(client):
    client.application.config.update(dict(
        secret_key='foo',
        server_name='www.example.com:8080',
        application_root='/test',
        session_cookie_domain='.example.com',
        session_cookie_httponly=False,
        session_cookie_secure=True,
        session_cookie_path='/'
    ))
    resp = client.get("/session")
    cookie = resp.headers['set-cookie'].lower()
    assert 'domain=.example.com' in cookie
    assert 'path=/;' in cookie
    assert 'secure' in cookie
    assert 'httponly' not in cookie

def test_basic_flashing(client, app):
    """test a session expiration"""
    app.config.secret_key = "foobar"
    resp = client.get("/flash?flash=hello")
    resp = client.get("/flash")
    assert resp.data == "[u'hello']" 

    # TODO: more flash testing with filters and categories

def test_multiple_handlers_and_flashing(client, app):
    """test what happens if we call a handler multiple times"""
    app.config.secret_key = "foobar"
    resp = client.get("/flash?flash=hello")
    assert app.last_handler.get_flashes()[0] == "hello"
    resp = client.get("/flash")
    assert len(app.last_handler.get_flashes()) == 0
    assert resp.data == "[u'hello']" 


