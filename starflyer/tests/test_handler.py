from starflyer.handler import Handler


def test_basic_handler():
    """test a handler implementation, rather simple right now as it's just a var store"""
    
    class MyHandler(Handler):
        def get(self):
            return {'app': self.app, 'request': self.request}
            
    request = "foobar"
    app = "app"
    handler = MyHandler(app=app, request=request)
    res = handler.get()
    assert res['request'] == request
    assert res['app'] == app
    
