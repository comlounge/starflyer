========
Snippets
========

Snippets are used within templates for plugins to extend content in predefined places without
the need to override the whole (master) template. 

A good example is the header section where plugins might want to add CSS or JS links of their own.

Defining snippets in a template
===============================

In order to use a snippet in a template you can simply render it like this (in Jinja2 syntax)::

    {{ snippets.header() }}

This will render all the snippets which have been registered for the name ``header``. You can pass
in any positional or keyword arguments you like. Of course all snippet providers for this snippet
need to accept those arguments as they will all be called in sequence with them.


Configuring snippets
====================

In order to tell starflyer which snippets are available you simply register them during
configuration time::

    config.register_snippet_names('header', 'footer')

Registering snippet providers
=============================

In order to add content to a snippet you need to register a snippets provider. For each snippet
name there can be more than one snippet provider. They will be called in turn and will add content 
subsequently to the snippet output.

Imagine you have a theme product and want to register a snippet in the head to include some additional
JS files. You would first write the snippet provider::

    def header(self, *args, **kwargs):
        return """<script src="/js/jquery.js" type="text/javascript"></script>"""

``params`` contains the parameters a template would usually get and you can use it
to construct your string or you might even call a template to render it (a comments sections
might be rendered that way).

``config`` is the configuration object which is active. You can use it to do database calls etc.

Next up you have to register that function in your ``setup()`` method ::

    from snippets import header
    config.snippets.header.append(header)






