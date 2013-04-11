from starflyer import Application, Handler, URL

import hello # import the module which has our view handler
import datetime
import os


class IndexHandler(Handler):
    """display the index document"""

    template = "index.html"

    def get(self):
        """retrieve the index template"""
        return self.render()

class ShortenHandler(Handler):
    """shorten a given URL"""

    def post(self):
         




class MyApplication(Application):
    """configure our application"""

    defaults = {
        'secret_key'    : os.random(20),
        'debug'         : True,
    }

    # 
    links = {}
    counter = 0

    # of course we need some routes
    routes = [
        URL("/",            "index",    IndexHandler),
        URL("/shortened",   "shorten",  ShortenHandler),
        URL("/<id>",        "url",      UrlHandler),
    ]


# create the app
def app(config):
    return MyApplication(__name__)

if __name__ == "__main__":
    myapp = app()
    myapp.run(debug=True, port=8889)


