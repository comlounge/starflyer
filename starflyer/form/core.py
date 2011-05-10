import types
import werkzeug

class RenderContext(object):
    """a render context which annotates a widget with a settings dict"""

    def __init__(self, widget, form):
        self.form = form
        self.widget = widget

    def __call__(self):
        """render the widget"""
        tag = self.widget.render(self)
        tmpl = self.form.tmpl_env.get_template("widget.html")
        error = self.form.errors.get(self.widget.name, None)
        return tmpl.render(data=self.widget, tag=tag, form = self.form, error=error)

class Widget(object):
    """a field base class which emits widgets"""

    BASE_ATTRS = ['type', 'name', 'css_class', 'id']
    ATTRS = []

    type = "text"
    css_class = ""

    def __init__(self, 
            name="",
            label=u"",
            description=u"",
            required=False,
            id = None,
            _charset = "utf-8",
            **kwargs):
        self.name = name
        if id is None:
            self.id = name
        else:
            self.id = id
        if type(label) is not types.UnicodeType:
            raise ValueError("label of field %s is not Unicode" %name)
        self.label = label
        if type(description) is not types.UnicodeType:
            raise ValueError("description of field %s is not Unicode" %name)
        self.description = description
        self.required = required
        self.additional = kwargs

    def render(self, context = None):
        """render this widget. We also pass in the ``RenderContext`` instance
        to be used in order to be able to access the ``Form`` instance and additional
        runtime information contained within."""
        attrs = {}
        for a in self.BASE_ATTRS+self.ATTRS:
            attrs[a] = getattr(self, a)
        attrs.update(self.additional)
        attrs['class'] = attrs['css_class']
        del attrs["css_class"]

        # process the value to be displayed
        if context.form.default.has_key(self.name):
            attrs['value'] = context.form.default[self.name]

        attrs = ['%s="%s"' %(a,werkzeug.escape(v, True)) for a,v in attrs.items()]
        attrs = " ".join(attrs)
        return u"<input {0} />".format(attrs)

    def __call__(self, form):
        """return a render context"""
        return RenderContext(self, form)


class Form(object):
    """a form"""

    error_css_class = "error"

    def __init__(self, tmpl_env, default = {}, values = {}, errors= {}, vocabs = {}):
        """initialize the form's widget. We pass in a ``tmpl_env`` which is a 
        ``jinja2.Environment`` and should contain a template called ``field.html``
        to be used for rendering a single field. Optionally you can pass in 
        ``vocabs`` which should contain the vocabularies to be used for select
        fields etc. ``default`` is a dictionary with which you can pass in data
        into the form as initial values."""
        print errors
        self.tmpl_env = tmpl_env
        self.vocabs = vocabs
        self.default = default
        self.values = values
        self.errors = errors
        self.data = {}
        for widget in self.widgets:
            self.data[widget.name] = widget

    def __getitem__(self, widget_name):
        """return a render context"""
        widget = self.data[widget_name]
        return widget(self)

    __getattr__ = __getitem__


