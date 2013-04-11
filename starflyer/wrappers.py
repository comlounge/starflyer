# -*- coding: utf-8 -*-
"""
    flask.wrappers
    ~~~~~~~~~~~~~~

    Implements the WSGI wrappers (request and response).

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.wrappers import Request as RequestBase, Response as ResponseBase
from werkzeug.utils import cached_property

from .exceptions import JSONBadRequest
from .helpers import json, _assert_have_json

class Request(RequestBase):
    """The request object used by default in Flask.  Remembers the
    matched endpoint and view arguments.

    It is what ends up as :class:`~flask.request`.  If you want to replace
    the request object used you can subclass this and set
    :attr:`~flask.Flask.request_class` to your subclass.

    The request object is a :class:`~werkzeug.wrappers.Request` subclass and
    provides all of the attributes Werkzeug defines plus a few Flask
    specific ones.
    """

    #: the internal URL rule that matched the request.  This can be
    #: useful to inspect which methods are allowed for the URL from
    #: a before/after handler (``request.url_rule.methods``) etc.
    #:
    #: .. versionadded:: 0.6
    url_rule = None

    #: a dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be `None`.
    view_args = None

    #: if matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~werkzeug.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

    #: this is the url adapter being used
    #: we store it here so we do not have to pass it around all the time.
    url_adapter = None

    @property
    def endpoint(self):
        """The endpoint that matched the request.  This in combination with
        :attr:`view_args` can be used to reconstruct the same or a
        modified URL.  If an exception happened when matching, this will
        be `None`.
        """
        if self.url_rule is not None:
            return self.url_rule.endpoint

    @cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.  Otherwise this will be `None`.

        This requires Python 2.6 or an installed version of simplejson.
        """
        if self.mimetype == 'application/json':
            request_charset = self.mimetype_params.get('charset')
            try:
                if request_charset is not None:
                    return json.loads(self.data, encoding=request_charset)
                return json.loads(self.data)
            except ValueError, e:
                return self.on_json_loading_failed(e)

    def on_json_loading_failed(self, e):
        """Called if decoding of the JSON data failed.  The return value of
        this method is used by :attr:`json` when an error ocurred.  The default
        implementation raises a :class:`JSONBadRequest`, which is a subclass of
        :class:`~werkzeug.exceptions.BadRequest` which sets the
        ``Content-Type`` to ``application/json`` and provides a JSON-formatted
        error description::

            {"description": "The browser (or proxy) sent a request that \
                             this server could not understand."}

        .. versionchanged:: 0.9
           Return a :class:`JSONBadRequest` instead of a
           :class:`~werkzeug.exceptions.BadRequest` by default.

        .. versionadded:: 0.8
        """
        raise JSONBadRequest()


class Response(ResponseBase):
    """The response object that is used by default in Flask.  Works like the
    response object from Werkzeug but is set to have an HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.response_class` to your subclass.
    """
    default_mimetype = 'text/html'
