from core import Processor, Error
import types

__all__ = ['String']

class String(Processor):
    """check if data is a string with the allowed properties""" 

    attrs = {
        'min_length' : 0, # minimum length of string
        'max_length' : None, # maximum length of string
        'strip' : True, # should string be stripped first?
        'required' : False, # check if the string is empty
        'default' : u'', # the default value
    }

    messages = {
        'wrong_type' : u'no string data detected',
        'too_short' : u'The provided string is too short, should be a minimum of %(min_length)s characters',
        'too_long' : u'The provided string is too long, should be a maximum of %(min_length)s characters',
        'required' : u'This field is required',
    }

    def __call__(self, ctx):
        """process the data."""
        data = ctx.data
        if data is None and self.required:
            self._error('required')
        if data is None:
            data = self.default
        if type(data) not in [types.StringType, types.UnicodeType]:
            self._error('wrong_type')
        if self.strip:
            data = data.strip()
        if len(data)==0 and self.required:
            self._error('required')
        if len(data)<self.min_length:
            self._error('too_short')
        if self.max_length is not None and len(data)>self.max_length:
            self._error('too_long')
        ctx.data = data
        return ctx

