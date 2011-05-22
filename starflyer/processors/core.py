import copy
from starflyer import AttributeMapper

__all__ = ['ProcessorContext', 'ProcessingException', 'Error', 'process', 
           'Processor']

class ProcessorContext(object):
    """a context for holding data and metadata during a processor chain call"""

    def __init__(self, data, **kw):
        """initialize the context with the initial data to process and
        some optional keyword args which might be used by some processor.

        ``data`` will be replaced by every processor, ``errors`` will contain
        a list of error which occurred during processing.
        
        """
        self.data = data 
        self.errors = []
        self.success = True
        self.attrs = AttributeMapper(copy.deepcopy(kw))

    def add_error(self, code, msg):
        self.errors.append({'code' : code, 'msg' : msg})
        self.success = False

# useful exceptions for controlling the processor flow

class ProcessingException(Exception):
    """base class for all processor related exceptions"""

    def __init__(self, code=None, msg=None):
        self.code = code
        self.msg = msg

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


def process(data, processors=[], **attrs):
    """run a list of ``Processor`` instances given in ``processors`` 
    on ``data``. The data will be stored in a ``ProcessorContext`` instance.

    It returns the ``ProcessorContext`` instance on success and failure. You can
    check the the ``success`` flag on the context to find out whether the run
    was successful or not. In case it was not you can find all the catched
    errors in the ``errors`` attribute of the context.

    :param data: the data on which the processors should run. It will be stored in a
                 newly created ``ProcessorContext`` instance which will then be passed
                 from processor to processor. Data can be anything as long as at least
                 the first processor understands it and converts it to something
                 usable for the next one etc.
    :param processors: A list of ``Processor`` instances which are run in sequence on 
                       the data passed in.
    :param attrs: A dictionary of additional attributes which will be passed to the
                ``ProcessorContext``. This is useful for e.g. passing in dynamic 
                data such as a session to predefined ``Processor`` instances.
                It is available to each processor via the ``attrs`` attribute of 
                the context instance. ``attrs`` is an ``AttributeMapper``.
    :return: returns a ``ProcessorContext`` instance with the result of the
        last processor stored in ``data``.
    """
    ctx = ProcessorContext(data, **attrs)
    for processor in processors:
        try:
            ctx = processor(ctx)
        except Error, e:
            ctx.add_error(e.code, e.msg)
            ctx.success = False
            return ctx
    return ctx

