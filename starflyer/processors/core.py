import copy

__all__ = ['ProcessorContext', 'ProcessingException', 'Break', 'Error', 'process']

class ProcessorContext(object):
    """a context for holding data and metadata during a processor chain call"""

    def __init__(self, data, **kw):
        """initialize the context with the initial data to process and
        some optional keyword args which might be used by some processor.

        ``data`` will be replaced by every processor, ``errors`` will contain
        a list of error which occurred during processing.
        
        """
        self.data = data 
        self.kw = kw
        self.errors = []
        self.success = True

    def add_error(self, code, msg):
        self.errors.append({'code' : code, 'msg' : msg})
        self.success = False

# useful exceptions for controlling the processor flow

class ProcessingException(Exception):
    """base class for all processor related exceptions"""

    def __init__(self, code=None, msg=None):
        self.code = code
        self.msg = msg


class Break(ProcessingException):
    """raise this if you want the processor chain to stop. Pass in an optional
    error message to the constructor."""

class Error(ProcessingException):
    """raise this if you just want to report an error. Pass in the error message
    to the constructor, e.g. ``Error(u'invalid data')`` """


# one processor object. These can be chained in a ProcessorChain.

class Processor(object):
    """base class for all processors"""

    attrs = {}
    messages = {}

    def __init__(self, **kwargs):
        """initialize the field's attributes by taking either a default
        value from the class ``attrs`` or from a passed in vale in ``kwargs``.
        The resulting value will be stored as instance attribute."""
        attrs = copy.copy(self.attrs)
        for a,v in attrs.items():
            setattr(self, a, kwargs.get(a,v))

    def _error(self, code):
        raise Error(code, self.messages[code] %self.__dict__)


def process(data, processors=[], **kw):
    """run all ``processors`` on ``data``. It will return 
    the ``ProcessorContext``instance which can then be checked for 
    ``errors`` or the ``success`` attribute."""
    ctx = ProcessorContext(data, **kw)
    for processor in processors:
        try:
            ctx = processor(ctx)
        except Break, e:
            ctx.add_error(e.code, e.msg)
            ctx.success = False
            return ctx
        except Error, e:
            ctx.add_error(e.code, e.msg)
            ctx.success = False
    return ctx

