class Events(object):
    """a container for holding event queues"""

    def __init__(self):
        """initialize the event container"""
        self.handlers = {} # mapping event name -> list of handlers

    def register(self, name, handler):
        """register a new handler for a given event

        :param name: the name of the event this handler should be triggered for
        :param handler: The handler to trigger which is a function
        """
        self.handlers.setdefault(name, []).append(handler)

    def handle(self, name, config, **kw):
        """handle an event by calling all registered handlers for it

        :param name: The name of the event which was triggered
            This should be usually of the form ``package.module:function``
        :param config: The global configuration object
        :param kw: optional keyword arguments to be passed to each handler
        """

        for handler in self.handlers.get(name, []):
            handler(name, config, **kw)
