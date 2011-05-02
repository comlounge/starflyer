from starflyer import asjson, ashtml, Handler

def test_html_decorator(handler):

    res = handler.html()
    assert res.headers['Content-Type'] == "text/html; charset=utf-8"
    assert res.data == """foobar"""


def test_json_method_decorator(handler):
    
    res = handler.json(3,4)
    assert res.headers['Content-Type'] == "application/json"
    assert res.data == """{"a": 3, "c": 17, "b": 4}"""
    
