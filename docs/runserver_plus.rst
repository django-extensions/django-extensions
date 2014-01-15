RunServerPlus
=============

:synopsis: RunServerPlus-typical runserver with Werkzeug debugger baked in


Introduction
------------

This item requires that you have the `Werkzeug WSGI utilities` (version 0.3)
installed.  Included with Werkzeug is a kick ass debugger that renders nice
debugging tracebacks and adds an AJAX based debugger (which allows code execution 
in the context of the traceback’s frames).  Additionally it provides a nice 
access view to the source code.


Getting Started
---------------

To get started we just use the *runserver_plus* command instead of the normal
*runserver* command::

  $ python manage.py runserver_plus

  * Running on http://127.0.0.1:8000/
  * Restarting with reloader...

  Validating models...
  0 errors found

  Django version 0.97-newforms-admin-SVN-unknown, using settings 'screencasts.settings'
  Development server is running at http://127.0.0.1:8000/
  Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
  Quit the server with CONTROL-C.

Note: all normal runserver options apply. In other words, if you need to change
the port number or the host information, you can do so like you would normally.


Usage
-----

Instead of the default Django traceback page, the Werkzeug traceback page 
will be shown when an exception occurs.

.. image:: https://f.cloud.github.com/assets/202559/1261027/2637f826-2c22-11e3-83c6-646acc87808b.png
    :alt: werkzeug-traceback

Along with the typical traceback information we have a couple of options. These
options appear when hovering over a particular traceback line.  Notice that
two buttons appear to the right:

.. image:: https://f.cloud.github.com/assets/202559/1261035/558ad0ee-2c22-11e3-8ddd-6678d84d77e7.png
    :alt: werkzeug-options

The options are:


View Source
^^^^^^^^^^^

This displays the source underneath the traceback:

.. image:: https://f.cloud.github.com/assets/202559/1261036/583c8c42-2c22-11e3-9eb9-5c16b8732512.png
    :alt: werkzeug-source

Being able to view the source file is handy because it provides more
context information around the error.  The actual traceback areas are 
highlighted so they are easy to spot.

One awkward aspect of th UI is that the page is not scrolled to the bottom.
At first I thought nothing was happening because of this.


Interactive Debugging Console
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Clicking on this button opens up a new pane under the traceback line
you're on. This is the money shot:

.. image:: https://f.cloud.github.com/assets/202559/1261037/5d12eda6-2c22-11e3-802a-2639ff8813fa.png
    :alt: werkzeug-debugger

An ajax based console appears in the pane and you can start debugging.
Notice in the screenshot above I did a `print environ` to see what was in the
environment parameter coming into the function.

*WARNING*: This should *never* be used in any kind of production environment.
Not even for a quick problem check.  I cannot emphasize this enough. The
interactive debugger allows you to evaluate python code right against the
server.  You've been warned.

.. _`Werkzeug WSGI utilities`: http://werkzeug.pocoo.org/


SSL
^^^

runserver_plus also supports SSL, so that you can easily debug bugs that to pop up 
when https is used. To use SSL simply provide a file name for certificates;  
a key and certificate file will be automatically generated::

  $ python manage.py runserver_plus --cert cert
  Validating models...
  0 errors found

  Django version 1.6.dev20130122125534, using settings 'mysite.settings'
  Development server is running at http://127.0.0.1:8000/
  Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
  Quit the server with CONTROL-C.
   * Running on https://127.0.0.1:8000/
   * Restarting with reloader
  Validating models...
  0 errors found

  Django version 1.6.dev20130122125534, using settings 'mysite.settings'
  Development server is running at http://127.0.0.1:8000/
  Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
  Quit the server with CONTROL-C.
  
After running this command, your web application can be accessed through 
https://127.0.0.1:8000. 

You will also find that two files are created in  the current working directory: 
a key file and a certificate file. If you run the above command again, these 
certificate files will be reused so that you do not have to keep accepting the 
self-generated certificates from your browser every time. You can also provide 
a specific file for the certificate to be used if you already have one::

  $ python manage.py runserver_plus --cert /tmp/cert 
  
Note that you need the OpenSSL library to use SSL, and Werkzeug 0.9 or later 
if you want to reuse existing certificates. 

To install OpenSSL::

  $ pip install pyOpenSSL
