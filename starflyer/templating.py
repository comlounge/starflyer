# -*- coding: utf-8 -*-
"""
    starflyer.templating
    ~~~~~~~~~~~~~~~~~~~~

    Implements the bridge to Jinja2.

    Adapted from flask and extended with our own module approach.

    :copyright: (c) 2011,2012 by Armin Ronacher, Christian Scholz.
    :license: BSD, see LICENSE for more details.
"""

from jinja2 import BaseLoader, Environment as BaseEnvironment, \
     TemplateNotFound


class DispatchingJinjaLoader(BaseLoader):
    """A loader that looks for templates in the application and all
    the blueprint folders.
    """

    def __init__(self, app):
        self.app = app

    def get_source(self, environment, template):
        for loader, local_name in self._iter_loaders(template):
            try:
                return loader.get_source(environment, local_name)
            except TemplateNotFound:
                pass

        raise TemplateNotFound(template)

    def _iter_loaders(self, template):
        
        # check if we are in the module namespace
        # thus we check the module first
        if template.startswith("_m"):
            parts = template.split("/")
            module_name = parts[1].lower()
            module = self.app.module_map[module_name]
            if module.module_jinja_loader is not None:
                yield module.module_jinja_loader, "/".join(parts[2:])

        # no namespace thus we check the app's loader first
        loader = self.app.jinja_loader
        if loader is not None:
            yield loader, template

        # in case nothing was found in the app, lets get back to modules
        for module in self.app.modules:
            if module.jinja_loader is not None:
                yield module.jinja_loader, template

    def list_templates(self):
        result = set()
        loader = self.app.jinja_loader
        if loader is not None:
            result.update(loader.list_templates())

        for module in self.app.modules:
            loader = module.jinja_loader
            if loader is not None:
                for template in loader.list_templates():
                    result.add(template)

        return list(result)



