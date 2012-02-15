from logbook import Handler, NOTSET, lookup_level

__all__ = ['MongoHandler']

class MongoHandler(Handler):
    """log to a mongoDB database """

    def __init__(self, collection, level=NOTSET, filter = None, bubble=False):
        """initialize with a mongodb collection

        :param collection: The MongoDB ``Collection`` object to log to.
        :param level: The level we log for
        :param filter: A filter to use
        :param bubble: defines if the log entry should bubble up
        
        """
        self.collection = collection
        self.level = lookup_level(level)
        self.bubble = bubble
        self.filter = filter

    def emit(self, record):
        """store the record in the database"""
        self.collection.insert(record.to_dict())

