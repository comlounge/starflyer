"""
some useful decorators
"""

import werkzeug
import functools
import json
import datetime

def jsonconverter(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(Obj), repr(Obj))


class ashtml(object):
    """takes a string output of a view and wraps it into a text/html response"""

    def __init__(self, charset="utf-8"):
        self.charset = charset

    def __call__(self, method):

        that = self 

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            response = werkzeug.Response(method(self, *args, **kwargs))
            response.content_type = "text/html; charset=%s" %that.charset
            return response
        return wrapper



class asjson(object):
    
    def __init__(self, **headers):
        self.headers = {}
        for a,v in headers.items():
            ps = a.split("_")
            ps = [p.capitalize() for p in ps]
            self.headers["-".join(ps)] = v
    
    def __call__(self, method):
        """takes a dict output of a handler method and returns it as JSON"""

        that = self
    
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            data = method(self, *args, **kwargs)
            s = json.dumps(data, default = jsonconverter)
            print self
            if self.request.args.has_key("callback"):
                callback = self.request.args.get("callback")
                s = "%s(%s)" %(callback, s)
                response = werkzeug.Response(s)
                response.content_type = "application/javascript"
            else:
                response = werkzeug.Response(s)
                response.content_type = "application/json"
            for a,v in that.headers.items():
                response.headers[a] = v
            return response

        return wrapper


