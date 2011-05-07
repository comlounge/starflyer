from core import Widget
import werkzeug

class Text(Widget):
    """a text input field"""

    type="text"
    size=10
    maxlength =100
    ATTRS = ['size','maxlength']

class Password(Text):
    """an password input field"""

    type="password"

class Email(Text):
    """a text widget"""

    type="email"

class URL(Text):
    """an URL input field"""

    type="url"

class Submit(Text):
    """an submit field"""

    type="submit"

class Select(Widget):
    """a select widget. In order to work this widget also needs
    a source for the options to display. As this list might be dynamically
    we cannot pass it to the ``Widget`` constructor but instead we will
    assume it to be retrieved from ``self.form.options[widget.name]()``"""

    ATTRS = ['multiple']
    multiple = None
    size = 1

    def render(self, context):
        """render this widget."""

        # create the select field
        attrs = {}
        for a in self.BASE_ATTRS+self.ATTRS:
            attrs[a] = getattr(self, a)
        attrs.update(self.additional)
        attrs['class'] = attrs['css_class']
        del attrs["css_class"]

        if attrs['multiple'] is None:
            del attrs['multiple']
        attrs = ['%s="%s"' %(a,werkzeug.escape(v, True)) for a,v in attrs.items()]
        attrs = " ".join(attrs)

        # add the options, this should return a list of tuples of (key, value)
        options = context.form.vocabs[self.name]
        if callable(options):
            options = options()
        options = ['<option value="%s">%s</option>' %(werkzeug.escape(a, True),werkzeug.escape(v, True)) for a,v in options]
        options = "\n".join(options)

        return u"<select {0}>{1}</select>".format(attrs, options)
