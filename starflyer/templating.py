# -*- coding: utf-8 -*-
"""
    starflyer.templating
    ~~~~~~~~~~~~~~~~~~~~

    Implements the bridge to Jinja2.

    Adapted from flask and extended with our own module approach.

    :copyright: (c) 2011-2013 by Armin Ronacher, Christian Scholz.
    :license: BSD, see LICENSE for more details.
"""

from jinja2 import BaseLoader, Environment as BaseEnvironment, \
     TemplateNotFound
import os

class DispatchingJinjaLoader(BaseLoader):
    """A loader that looks for templates in the application and all
    the modules.
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
        """iterate over all the loaders, both from application and from modules.

        Application loaders will always have precedence and can also override module templates. 
        """
        
        # first check the application loader
        loader = self.app.jinja_loader
        if loader is not None:
            yield loader, template

        # now that we didn't find it in there lets go over all the module related ones
        # but only if they are prefixed with _m
      
        if template.startswith("_m"):
            path = template.split("/")
            dummy, module_name = path[:2]
            template = os.path.join(*path[2:])
            module = self.app.module_map[module_name]
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



