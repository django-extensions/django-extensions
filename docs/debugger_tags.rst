Debugger tags
=============

:synopsis: Allows you to use debugger breakpoints on Django templates.

Introduction
------------

These templatetags makes debugging Django templates easier. You can choose between ipdb, pdb or wdb filters.

Usage
-----

Make sure that you loaded `debugger_tags` like::

   {% load debugger_tags %}

Now, you're ready to use debugger filters inside a template::

   {% for object in object_list %}
      {{ object|ipdb }}  
   {% endfor %}

When rendering a template ipdb session will be started.
