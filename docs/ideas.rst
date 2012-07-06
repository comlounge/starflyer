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
