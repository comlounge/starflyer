# -*- coding: utf-8 -*-
"""

    as it has all we need, simply copied over from flask.

    :copyright: (c) 2011 by Armin Ronacher, Christian Scholz
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime
from werkzeug.contrib.securecookie import SecureCookie

class Cookie(SecureCookie):
    """our own cookie implementation which not only stores the payload but
    also metadata such as lifetime etc. We need to store it here because
    in handlers we can remember it that way for the app which then sets
    it on the response."""

    def __init__(self, key, data=None, secret_key=None, new=True,
        expires=None, session_expires=None, max_age=None, path='/', 
        domain=None, secure=None, httponly=False, force=False):
        super(Cookie, self).__init__(data, secret_key, new)
        self.key = key
        self.expires = expires
        self.session_expires = session_expires
        self.max_age = max_age
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly
        self.force = force
        self.modified = True

    def save(self, response):
        """save this cookie"""
        self.save_cookie(response, 
            key=self.key, 
            expires=self.expires, 
            session_expires=self.session_expires, 
            max_age=self.max_age, 
            path=self.path,
            domain=self.domain, 
            secure=self.secure, 
            httponly=self.httponly, 
            force=True)
        

class SessionMixin(object):
    """Expands a basic dictionary with an accessors that are expected
    by Flask extensions and users for the session.
    """

    def _get_permanent(self):
        return self.get('_permanent', False)

    def _set_permanent(self, value):
        self['_permanent'] = bool(value)

    #: this reflects the ``'_permanent'`` key in the dict.
    permanent = property(_get_permanent, _set_permanent)
    del _get_permanent, _set_permanent

    #: some session backends can tell you if a session is new, but that is
    #: not necessarily guaranteed.  Use with caution.  The default mixin
    #: implementation just hardcodes `False` in.
    new = False

    #: for some backends this will always be `True`, but some backends will
    #: default this to false and detect changes in the dictionary for as
    #: long as changes do not happen on mutable structures in the session.
    #: The default mixin implementation just hardcodes `True` in.
    modified = True

class SecureCookieSession(SecureCookie, SessionMixin):
    """Expands the session with support for switching between permanent
    and non-permanent sessions.
    """


class NullSession(SecureCookieSession):
    """Class used to generate nicer error messages if sessions are not
    available.  Will still allow read-only access to the empty session
    but fail on setting.
    """

    def _fail(self, *args, **kwargs):
        raise RuntimeError('the session is unavailable because no secret '
                           'key was set.  Set the secret_key on the '
                           'application to something unique and secret.')
    __setitem__ = __delitem__ = clear = pop = popitem = \
        update = setdefault = _fail
    del _fail


class SessionInterface(object):
    """The basic interface you have to implement in order to replace the
    default session interface which uses werkzeug's securecookie
    implementation.  The only methods you have to implement are
    :meth:`open_session` and :meth:`save_session`, the others have
    useful defaults which you don't need to change.

    The session object returned by the :meth:`open_session` method has to
    provide a dictionary like interface plus the properties and methods
    from the :class:`SessionMixin`.  We recommend just subclassing a dict
    and adding that mixin::

        class Session(dict, SessionMixin):
            pass

    If :meth:`open_session` returns `None` Flask will call into
    :meth:`make_null_session` to create a session that acts as replacement
    if the session support cannot work because some requirement is not
    fulfilled.  The default :class:`NullSession` class that is created
    will complain that the secret key was not set.

    To replace the session interface on an application all you have to do
    is to assign :attr:`flask.Flask.session_interface`::

        app = Flask(__name__)
        app.session_interface = MySessionInterface()

    .. versionadded:: 0.8
    """

    #: :meth:`make_null_session` will look here for the class that should
    #: be created when a null session is requested.  Likewise the
    #: :meth:`is_null_session` method will perform a typecheck against
    #: this type.
    null_session_class = NullSession

    def make_null_session(self, app):
        """Creates a null session which acts as a replacement object if the
        real session support could not be loaded due to a configuration
        error.  This mainly aids the user experience because the job of the
        null session is to still support lookup without complaining but
        modifications are answered with a helpful error message of what
        failed.

        This creates an instance of :attr:`null_session_class` by default.
        """
        return self.null_session_class()

    def is_null_session(self, obj):
        """Checks if a given object is a null session.  Null sessions are
        not asked to be saved.

        This checks if the object is an instance of :attr:`null_session_class`
        by default.
        """
        return isinstance(obj, self.null_session_class)

    def get_cookie_domain(self, app):
        """Helpful helper method that returns the cookie domain that should
        be used for the session cookie if session cookies are used.
        """
        if app.config.get('session_cookie_domain') is not None:
            return app.config.session_cookie_domain
        if app.config.get('server_name') is not None:
            # chop of the port which is usually not supported by browsers
            return '.' + app.config.server_name.rsplit(':', 1)[0]

    def get_cookie_path(self, app):
        """Returns the path for which the cookie should be valid.  The
        default implementation uses the value from the SESSION_COOKIE_PATH``
        config var if it's set, and falls back to ``APPLICATION_ROOT`` or
        uses ``/`` if it's `None`.
        """
        return app.config.get('session_cookie_path') or \
               app.config.get('application_root') or '/'

    def get_cookie_httponly(self, app):
        """Returns True if the session cookie should be httponly.  This
        currently just returns the value of the ``session_cookie_httponly``
        config var.
        """
        return app.config.get('session_cookie_httponly', False)

    def get_cookie_secure(self, app):
        """Returns True if the cookie should be secure.  This currently
        just returns the value of the ``session_cookie_secure`` setting.
        """
        return app.config.get('session_cookie_secure', False)

    def get_expiration_time(self, app, session):
        """A helper method that returns an expiration date for the session
        or `None` if the session is linked to the browser session.  The
        default implementation returns now + the permanent session
        lifetime configured on the application.
        """
        if session.permanent:
            return datetime.utcnow() + app.config.permanent_session_lifetime

    def open_session(self, app, request):
        """This method has to be implemented and must either return `None`
        in case the loading failed because of a configuration error or an
        instance of a session object which implements a dictionary like
        interface + the methods and attributes on :class:`SessionMixin`.
        """
        raise NotImplementedError()

    def save_session(self, app, session, response):
        """This is called for actual sessions returned by :meth:`open_session`
        at the end of the request.  This is still called during a request
        context so if you absolutely need access to the request you can do
        that.
        """
        raise NotImplementedError()


class SecureCookieSessionInterface(SessionInterface):
    """The cookie session interface that uses the Werkzeug securecookie
    as client side session backend.
    """
    session_class = SecureCookieSession

    def open_session(self, app, request):
        key = app.config.get('secret_key', None)
        if key is not None:
            session = self.session_class.load_cookie(request,
                                                  app.config.session_cookie_name,
                                                  secret_key=key)
            return session
        else:
            print "*** CANNOT OPEN SESSION BECAUSE SECRET KEY IS MISSING IN THE CONFIGURATION"

    def save_session(self, app, session, response):
        """save a session"""
        expires = self.get_expiration_time(app, session)
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        if session.modified and not session:
            response.delete_cookie(app.config.session_cookie_name, path=path,
                                   domain=domain)
        else:
            if hasattr(response, "set_cookie"):
                session.save_cookie(response, app.config.session_cookie_name, path=path,
                                expires=expires, httponly=httponly,
                                secure=secure, domain=domain)
