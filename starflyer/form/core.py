import types
import werkzeug

class RenderContext(object):
    """a render context which annotates a widget with a settings dict"""

    def __init__(self, widget, form):
        self.form = form
        self.widget = widget

    def __call__(self, widget_attrs={}, field_attrs={}, template=None):
        """render the widget. This will be called form within
        the template. You can pass additional parameters for both 
        the widget (e.g. the actual input tag) in ``widget_attrs`` 
        and the field (the surrounding structure with label etc.)
        in ``field_attrs``.

        If you wish you can also pass a new template name for the field
        to be used in ``template``. It defaults to the name define in 
        ``widget_template`` in the form class. 
        
        """
        if template is None:
            template = self.form.widget_template
        tag = self.widget.render(self, **widget_attrs)
        tmpl = self.form.template_env.get_template(template)
        error = self.form.errors.get(self.widget.name, None)
        return tmpl.render(data=self.widget, tag=tag, form = self.form, error=error, **field_attrs)

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

    def get_value(self, form):
        """return the value to be displayed inside the widget. This will either
        come from the ``defaults`` attribute of the form or it`s ``values`` dict.
        The former will usually be populated with data from an database record and
        the latter will be populated from a previous form input, e.g. on an error
        condition on a different widget."""

        _no_value = object()

        n = self.name
        value = form.values.get(n, _no_value)
        if value is _no_value:
            value = form.default.get(n, u'')
        return value
        
    def render(self, render_context = None, add_class="", **kwargs):
        """render this widget. We also pass in the ``RenderContext`` instance
        to be used in order to be able to access the ``Form`` instance and additional
        runtime information contained within.

        Additionally you can provide an ``add_class`` parameter which can contain
        a class name to be added to the CSS classes for the input tag

        Any additional keyword arguments passed will override the original attributes
        used for rendering the tag

        Note that this method will only input e.g. a input tag and not the
        surrounding divs etc.
        """
        attrs = {}
        for a in self.BASE_ATTRS+self.ATTRS:
            attrs[a] = getattr(self, a)
        attrs.update(self.additional)
        attrs.update(kwargs)
        attrs['class'] = attrs['css_class']+" "+add_class
        del attrs["css_class"]

        # process the value to be displayed
        attrs['value'] = self.get_value(render_context.form)

        attrs = ['%s="%s"' %(a,werkzeug.escape(v, True)) for a,v in attrs.items()]
        attrs = " ".join(attrs)
        return u"<input {0} />".format(attrs)

    def __call__(self, form):
        """return a render context"""
        return RenderContext(self, form)


class Form(object):
    """a form"""

    error_css_class = "error"
    widget_template = "widget.html"
    widgets = [] # list of Widget instances

    def __init__(self, 
                 template_env=None, 
                 default = {}, 
                 values = {}, 
                 errors= {}, 
                 vocabs = {}):
        """initialize the form's widget. We pass in a ``tmpl_env`` which is a 
        ``jinja2.Environment`` and should contain a template called ``field.html``
        to be used for rendering a single field. Optionally you can pass in 
        ``vocabs`` which should contain the vocabularies to be used for select
        fields etc. ``default`` is a dictionary with which you can pass in data
        into the form as initial values."""
        self.template_env = template_env
        self.vocabs = vocabs
        self.default = default # this might come from an object
        self.values = values # this might come from a form and overrides the defaults
        self.errors = errors
        self.data = {}
        for widget in self.widgets:
            self.data[widget.name] = widget

    def __getitem__(self, widget_name):
        """return a render context"""
        widget = self.data[widget_name]
        return widget(self)

    __getattr__ = __getitem__

    def process(self, **kw):
        """run the processors on all widgets"""


