Template handling in starflyer
==============================

We have the following source for templates:

- application
- modules 

All of these templates are merged together into a single jinja2 Environment/loader but with different prefixes.

Application templates usually reside in the ``templates/`` folder in the application directory and are accessed on the top level path.
Thus ``index.html`` will be search in ``templates/index.html`` and ``admin/index.html`` will be search in ``templates/admin/index.html`` on the filesystem.

Modules have their templates in their own subfolder inside the module directory. It is called ``templates/``, too. To access a template from a module's
handler you can use a simple path like ``index.html`` which will access ``templates/index.html`` inside the module's folder. 

From a module you can also access templates from the application or other modules. These are basically just a level up. e.g.

- to access a template from the application, refer to it as ``/index.html`` or ``../index.html``
- to access a template from a different module, refer to it prefix by the module name, e.g. ``../othermodule/index.html´´
- you can also use an absolute path to access a module template directly: ``/_m/othermodule/index.html``

Overriding module templates
---------------------------

You can override any module template from within the application by simply creating a new folder ``templates/_m/<modulename>`` for the module with name ``modulename`` and
placing templates in there. This will always have precedence over the module template.


Implementation
--------------

The following sources for templates exists:

- application templates under /
- module related templates under _m/<prefix>


