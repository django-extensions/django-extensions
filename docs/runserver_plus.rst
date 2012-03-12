RunServerPlus
=============

:synopsis: RunServerPlus-typical runserver with Werkzeug debugger baked in


Introduction
------------

This item requires that you have the `Werkzeug WSGI utilities` (version 0.3)
installed.  Included with Werkzeug is a kick ass debugger that renders nice
debugging tracebacks and adds an AJAX based debugger (which allows to execute
code in the context of the traceback’s frames).  Additionally it provides a
nice access view to the source code.


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


Using
-----

Whenever we hit an exception in our code, instead of the normal Django
traceback page appearing, we see the Werkzeug traceback page instead.

http://blog.michaeltrier.com/media/assets/2008/6/22/werkzeug-traceback.png

Along with the typical traceback information we have a couple of options. These
options appear when you hover over a particular traceback line.  Notice that
two buttons appear to the right:

http://blog.michaeltrier.com/media/assets/2008/6/22/werkzeug-options.png

The options are:


View Source
^^^^^^^^^^^

This displays the source below the traceback:

http://blog.michaeltrier.com/media/assets/2008/6/22/werkzeug-source.png

Being able to view the source file is handy because you are able to get more
context information around where the error occurred.  The actual traceback
areas are highlighted so they are easy to spot.

One awkward piece about this is that the page is not scrolled to the bottom.
At first I thought nothing was happening because of this.


Interactive Debugging Console
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you click on this button a new pane will open up below the traceback line
you're on. This is the money shot:

http://blog.michaeltrier.com/media/assets/2008/6/22/werkzeug-debugger.png

An ajax based console appears in the pane and you can begin debugging away.
Notice in the screenshot above I did a `print environ` to see what was in the
environment parameter coming into the function.

*WARNING*: This should *never* be used in any kind of production environment.
Not even for a quick check into a problem.  I cannot emphasize this enough. The
interactive debugger allows you to evaluate python code right against the
server.  You've been warned.

.. _`Werkzeug WSGI utilities`: http://werkzeug.pocoo.org/
