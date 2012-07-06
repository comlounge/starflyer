=================================
starflyer setup and configuration
=================================

Configuration of starflyer means two things: Wiring the application and handling user configurable stuff. The first one we call ``setup`` and the latter ``configuration``

Of course the two are very much related as you might need some configuration before you can wire things (e.g. you need to know which database to use before you can instantiate the database classes).

Configuration
=============

Configuration usually means that an administrator can define things like the host and port of a database, which cookie secret to use, where to log to and so on. Depending on the application it might also mean that some component can be switched on or off etc.

Usually the act of configuration is that you pass some data to the application wich typically is stored in some configuration file, like some .ini.

In starflyer you can use an ini file which looks basically like this::

    app:
        setup: myapp:default

    server:
        port: 9003

    config:
        debug: True
        virtual_host: https://192.168.78.22/services/

As you can see there are different sections which contain various configuration options. 

The ``app`` section
-------------------

The application section basically defines which setup method to use (see below for setup). This needs to be an entry point which you have to declare in your product. Usually the setup of the Python package itself is used but you are free to define your own package and override the complete setup routine. Usually this is not recommended and should only be used if you really run out of options.

.. warning:: Overriding the setup routine will likely break on future updates of the original product. 

The ``server`` section
----------------------

The server section contains information for the integrated WSGI server (it's the werkzeug one) in case you are using it. It can contain the following items:

``host`` - the ip address the server is listening to (defaults to ``0.0.0.0``)
``port`` - theport the server is listening on (defaults to 8080)


The ``config`` section
----------------------

This is the actual app specific configuration section. The available items depens on the application you use and should be documented in it's documentation. Usually at least a ``virtual_host`` item is available with which you can let the application run under a different URL.


Setup
=====

The setup is the part where the application developer stitches together the application from it's pieces. Here we will find routing information, database setup, template location setup, sub application setup and so on. 

The setup is created in a ``setup()`` function which is defined as entry point for the python package containing your application. This looks like this in setup.py in your package root::

    entry_points="""
        [starflyer.config]
        default = myapp.appsetup:setup
        [paste.app_factory]
        main = starflyer:run
    """

In order to setup your application you have to derive from the ``starflyer.AppSetup`` class and provide those methods you care about. This class also will have
some useful predefined methods you can choose to use or to overwrite if you need to.

Here is a small example which would live in your ``myapp/myapp/appsetup.py`` file::

    import starflyer
    import pymongo

    def setup():

        # create the app


    class Setup(starflyer.AppSetup):
        """setup our application"""

        # default template name in case of simple templating setup
        template_dir = "mytemplates"

        # defaults for user configurable options. Can be overridden by .ini-file or environment
        # there might also be defaults from the AppSetup class for integrated functionality
        defaults = {
            'title' : "My Test Application",
            'flash_cookie_name' : 'm'
        }

        def setup(self):
            """add additional setup as you see fit"""
            self.db = pymongo.Connection()

There are several methods you can overwrite which are documented later.  

Configuration options
---------------------

Let us first talk about the configuration options which a user can set. As we saw above you can define some in your applications ini-file. These are then read by the setup code.
If they are not given, the data in the ``defaults`` dictionary is used. If it's missing there and it's functionality provided by starflyer itself, then starflyer itself will
provide a default. Additionally you can override these values via environment variables. These have to be written in upper case while the configuration values are
supposed to be all lowercase. 

So the sequence of importance is:

1. starflyer default (if given)
2. setup class default
3. ini file
4. environment variable

In a handler you can use these configuration values like this::

    title = self.config.title

So basically they are all contained in the ``config`` object which is passed to every handler and is read-only.



Templates
---------

One of the pre-defined components of starflyer are the templates which are based on Jinja2. Of course, in order to use it, you have to tell starflyer where to find the templates.
At least if you want to use a different location than the pre-defined one which points to ``templates/`` in your package base directory. 

To set the template location by path you can simply set the ``template_dir`` class variable as you can see in the example above. If you have a relative path then it will be relative to your
python package, an absolute path will just use the directory directly. 

You can also choose to use an advance setup for your templates, e.g. if you want to use something different than the Jinja2 ``PackageLoader``. In order to do that you have to
override the ``setup_templates()`` method::

    def setup_templates(self):
        """setup the templates"""

        self.templates = Environment(ChoiceLoader([
            FileSystemLoader('/path/to/user/templates'),
            FileSystemLoader('/path/to/system/templates')
        ]))


So basically you have to build the Jinja2 environment and store it into the ``templates`` instance variable. In case you need multiple environments you can of course also
define additional template configurations and store it in additional instance variables. 


Routes
------

Routes are based on the Werkzeug routing system and this means that route definitions basically consist of the following data:

- a regular expression which has to match and might contain variables
- an endpoint name, basically a name for the route
- a view class which is going to handle the view
- optional attributes

You can define these routes in several ways:

1. As a fixed class variable of the ``Configuration`` instance
2. Using a method called ``setup_routes`` of the ``Configuration`` instance
3. Adding routes later dynamically (although not recommended)+

Defining routes as class variables
##################################


In this case you simply list the route definitions as follows::

    routes = [
        ("/about", "about", about.About),
        ("/post/<id>", "post", post.Post),
        ("/post/<id>/comments", "comments", comments.Comments),
        ("/post/<id>/comments/<cid>", "comment", comments.Comment),
    ]

And so on. Of course you have to import the modules containing the view classes before. If you want to give options you can do so by adding a dictionary to the tuple. 

Additionally you can omit the view class. In this case you need to map a class to the endpoint name later, e.g.::

    routes = [
        ("/post/<id>", "post")
    ]
    
    views = {
        "post" : post.Post,
    }

This of course makes more sense if you set this up more dynamically. 


Defining routes via the setup method
####################################

This works similar but inside a method like this::

    def setup_routes(self):
        self.add_route("/post/<id>", "post", post.Post)
        self.add_route("/comment/<cid>", "comment")

The same basically applies like above including the possibility to do the view mapping separately::

    def setup_views(self):
        self.add_view("comment", comment.Comment)

This version might come in handy if you have dynamically find out what the right view class to use is e.g. if the user can configure something.

Adding route dynamically
########################

not sure yet if this should be supported (and if we need to do something for it like recompiling or so)

We need to update the map after a change at least.



Static files
------------

Per default ``static/`` in your package is used but you can override with a class variable inside the setup::

    static_dir = "/some/where/on/my/filesystem"

Additionally you can define the URL name for it the same way (also defaulting to ``/static``)::

    static_url = "/assets"







Sub applications
----------------

Sometimes you might want to use some sub application from  another python package, e.g. for providing user registration out of the box. These applications have their own setup method and we need to merge these in. Especially the routes are important to merge and usually those sub applications run under a prefixed url namespace.

What do we need sub applications for?
#####################################

Imagine a blogging application which wants to embed user management from a different package. Those two packages are not completely separate from each other. Here is where they might meet:

- There are URLs mounted in e.g. ``/users/`` which are then processed by the user manager
- There needs to be some passing of login information via some session
- The host application needs to be able to incorporate the login form etc. in it's own view. Processing of input might be either done by the host or sub application
- The host application needs to be able to configure the user manager
- 

::

    from userbase import setup

    userbase_setup = setup({
        db = db, 
        user_collection = "users", 
        cookie_name = "u",
    })


Ideas:

- should an app be able to define it's own setup methods? (setup_form ?)
- or maybe passing something in is enough? (userbaseapp.config.form_class = LoginForm)
- how can a sub application be mounted? Should it be the configured app object? 
- simply use WSGI dispatch? (maybe easiest). 





TBD


Module based routes
-------------------

- better organization to use some __init__.py file 
- need to include those with a prefix maybe





