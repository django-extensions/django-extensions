Debugger tags
=============

:synopsis: Allows you to use debugger breakpoints on Django templates.

Introduction
------------

These templatetags make debugging Django templates easier.
You can choose between ipdb, pdb or wdb filters.

Usage
-----

Make sure that you load `debugger_tags`::

    {% load debugger_tags %}

Now, you're ready to use debugger filters inside a template::

    {% for object in object_list %}
        {{ object|ipdb }}
    {% endfor %}

When rendering the template an ipdb session will be started.
