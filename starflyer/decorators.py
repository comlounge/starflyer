"""
some useful decorators
"""

import werkzeug
import functools
import json
import datetime

__all__=['asjson', 'render']


def jsonconverter(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        # skip it otherwise
        return None
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

class render(object):
    """a decorator which takes a dictionary from the wrapped function
    and pushes this into the handlers render() method.
    """

    def __init__(self, tmplname=None, charset="utf-8", **headers):
        """initialize the render decorator

        :param tmplname: The template name to use for rendering
        :param charset: The charset to set
        """
        self.charset = charset
        self.tmplname = tmplname
        self.headers = {}
        for a,v in headers.items():
            ps = a.split("_")
            ps = [p.capitalize() for p in ps]
            self.headers["-".join(ps)] = v

    def __call__(self, method):

        that = self 

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            self.response.content_type = "text/html; charset=%s" %that.charset
            args = method(self, *args, **kwargs)
            self.response.data = self.render(tmplname = that.tmplname, **args)
            self.response.set_cookie('m', self._encode_messages(self.messages_out))
        return wrapper


class asjson(object):
    
    def __init__(self, cls=None, **headers):
        self.headers = {}
        self.cls = cls
        for a,v in headers.items():
            ps = a.split("_")
            ps = [p.capitalize() for p in ps]
            self.headers["-".join(ps)] = v
    
    def __call__(self, method):
        """takes a dict output of a handler method and returns it as JSON wrapped in a Response"""

        that = self
    
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            data = method(self, *args, **kwargs)
            response = self.app.response_class()
            if that.cls is None:
                s = json.dumps(data, default = jsonconverter)
            else:
                s = json.dumps(data, cls = that.cls)
            if self.request.args.has_key("callback"):
                callback = self.request.args.get("callback")
                s = "%s(%s)" %(callback, s)
                response.data = s
                response.content_type = "application/javascript"
            else:
                response.data = s
                response.content_type = "application/json"
            for a,v in that.headers.items():
                response.headers[a] = v
            return response

        return wrapper


