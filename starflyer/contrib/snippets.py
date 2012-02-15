"""
Snippet helpers
"""

def css_link(config, *paths):
    """create a CSS link snippet provider

    :param config: the configuration object
    :param paths: A list of paths CSS files to include
    """

    def snippet(*args, **kwargs):
        return "\n".join(["""<link href="{}" rel="stylesheet">""".format(path) for path in paths])

    return snippet


