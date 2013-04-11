Ideas
=====

Request dispatching
-------------------

0. Create the Request object and do the matching. Store all retrieved data in the handler to be instantiated. If no match was found, store a routing exception in the request. An exception should be raised which can be catched somewhere but not sure where ;-)
1. If we need to run something before the first request and this is it, run it. 
2. Run the url value preprocessors which can change the url values somehow. But we also keep the original. It might e.g. remove a language code and store it somewhere else.
3. Run the request preprocessors. If they return a request value instead of None we will use that for a Response and stop further request processing.
4. Dispatch to the right method which returns some value
5. Do something like make_response in flask to create a response object. You might still be able to control what happens by a decorator which can store information in the request handler on which make_response is called then. This will return a Response object in any case.
6. Some hooks for postprocessing the Response object are called. Also decorators can have their say here, e.g. for changing some headers. 
7. Signals are sent for the processing ending. 
8. The response is returned and we are finished.






Request in flask
----------------
They are stored in the request context and contain the following:

- the Request object
- The url adapter. This is from werkzeug and either instantiated with the request given already or from predefined server name, script and scheme. (see app.py). 
- flashes and sessions
- functions to be called after the request (good idea to maybe inject them in a handler but can be done by the class as well)
- it has a method ``match_request`` which does the URL matching. Stores ``url_route`` and ``view_args`` in the request.
- matching is done on initialization



Modules
-------

Modules can implement additional functionality for starflyer. This includes:

- they can add new instance variables to handlers
- they can provide additional routes, maybe prefixed
- they can provide additional templates


Implementing a module
*********************

A modules is a class subclassed from ``starflyer.Module`` which implements all the necessary hooks and configuration options. 



Adding new routes
*****************




Adding new templates
********************

A module can provide new templates which even can reuse existing master templates. Thus a module can take over a full part of a website, such as a user manager or admin backend.

To do this you first need to define the routes for these screens in your module::

    routes = [
        URL("/user_add", "user_add", views.users.Add)
    ]

Now that you have a route you can implement it with a normal handler::


    class Add(Handler): 
        """handle user add"""

        template = "_m/usermanager/addform.html"

        def get(self):
            """show the user add form"""

            form = self.somehow_generate_the_form()
            return self.render(form = form)
        

Here we are using the template at ``_m/usermanager/addform.html``. This is namespaced meaning that under ``_m`` all the modules will have their own template
namespace. Next up is the name of the module we are going to use, here ``usermanager``. And after that is the template name local to the usermanager instance. 

The template itself might look like this::


    {% extend M.master_template %}

    {% block M.content_block %}
        
        <h1>Add new user</h1>

        {{form}}

    {% endblock %}


Now this template uses interesting things like ``M.master_template`` or ``M.content_block``. ``M`` in this case is the module instance and thus you are
basically using properties of this module. What they return can be configured on module instantiation.

That way the hosting application can configure what the names of the master and blocks are. 



Injecting app paramaters into templates
***************************************

Using a master template probably means that it expects some global or local parameters which are not available when called from a module. 

In order to solve this an application needs to use context hooks in which they compute all the information necessary to render a template. Those hooks
are basically functions which are called during handler instantiation and which can then compute data put it into a context object which then is available
to the handler and in the global handler namespace.

Thus if you want to retrieve user information or permissions in order to know what to display in the master template you can use the context object. 

Defining it is easy as you only do this once in the application object::


    class MyApp(Application):
        
        
        def get_handler_context(self, request):
            """compute context information"""
            
            username = somehow_compute_username()
            permissions = somehow_compute_permissions()

            return Context(
                username = username,
                permissions = permissions,
            )


Inside a template you can use it like this::

    {{ C.username }}

As you can see we use a global variable called ``C``.

.. info:: 

    In a future version you might also be able to extend the context via event handlers





Sub mounting routes
===================

Sometimes it might be useful to collect some URLs together and "submount" them with a prefix. E.g. you might 
want to register URLs inside a sub directory of your app and want to register them under a common prefix. 

To do this you first need to define the routes in your sub folder like ``users/``::


    routes = [
        URL("/", "list", views.ListView),
        URL("/<user>", "user", views.UserView),
    ]


000.033.000
080.033









