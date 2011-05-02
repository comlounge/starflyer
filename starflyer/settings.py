
class AttributeMapper(dict):
    """a dictionary like object which also is accessible via getattr/setattr"""

    def __getattr__(self, k):
        """retrieve some data from the dict"""
        if self.has_key(k):
            return self[k]
        raise AttributeError(k)

    def __setattr__(self, k,v):
        """store an attribute in the map"""
        dict.__setattr__(self,k,v)


