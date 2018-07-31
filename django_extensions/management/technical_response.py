# -*- coding: utf-8 -*-
import six
from django.core.handlers.wsgi import WSGIHandler

wsgi_tb = None


def null_technical_500_response(request, exc_type, exc_value, tb, status_code=500):
    """Function to override django.views.debug.technical_500_response.

    Django's convert_exception_to_response wrapper is called on each 'Middleware' object to avoid
    leaking exceptions. The wrapper eventually calls technical_500_response to create a response for
    an error view.

    Runserver_plus overrides the django debug view's technical_500_response function with this
    to allow for an enhanced WSGI debugger view to be displayed. However, because Django calls
    convert_exception_to_response on each object in the stack of Middleware objects, re-raising an error
    quickly pollutes the traceback displayed.

    Runserver_plus only needs needs traceback frames relevant to WSGIHandler Middleware objects, so
    only raise the traceback if it is for a WSGIHandler. If an exception is not raised here, Django
    eventually throws an error for not getting a valid response object for its debug view.
    """
    global wsgi_tb

    # After an uncaught exception is raised the class can be found in the second frame of the tb
    if isinstance(tb.tb_next.tb_frame.f_locals['self'], WSGIHandler):
        wsgi_tb = tb
        six.reraise(exc_type, exc_value, tb)
    else:
        six.reraise(exc_type, exc_value, wsgi_tb)
