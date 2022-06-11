# -*- coding: utf-8 -*-
import threading

from django.core.handlers.wsgi import WSGIHandler

tld = threading.local()
tld.wsgi_tb = None


def null_technical_500_response(request, exc_type, exc_value, tb, status_code=500):
    """
    Alternative function for django.views.debug.technical_500_response.

    Django's convert_exception_to_response() wrapper is called on each 'Middleware' object to avoid
    leaking exceptions. If an uncaught exception is raised, the wrapper calls technical_500_response()
    to create a response for django's debug view.

    Runserver_plus overrides the django debug view's technical_500_response() function to allow for
    an enhanced WSGI debugger view to be displayed. However, because Django calls
    convert_exception_to_response() on each object in the stack of Middleware objects, re-raising an
    error quickly pollutes the traceback displayed.

    Runserver_plus only needs needs traceback frames relevant to WSGIHandler Middleware objects, so
    only store the traceback if it is for a WSGIHandler. If an exception is not raised here, Django
    eventually throws an error for not getting a valid response object for its debug view.
    """
    try:
        # Store the most recent tb for WSGI requests. The class can be found in the second frame of the tb
        if isinstance(tb.tb_next.tb_frame.f_locals.get('self'), WSGIHandler):
            tld.wsgi_tb = tb
        elif tld.wsgi_tb:
            tb = tld.wsgi_tb
    except AttributeError:
        pass

    try:
        if exc_value is None:
            exc_value = exc_type()
        if exc_value.__traceback__ is not tb:
            raise exc_value.with_traceback(tb)
        raise exc_value
    finally:
        exc_value = None
        tb = None
