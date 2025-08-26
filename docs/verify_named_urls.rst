verify_named_urls
=================

:synopsis: Verify named URLs in templates

This command will check whether the templates in your apps have matching named
URLs defined in your views.

For example this template, when rendered, would result in a 500 on your site:

::

    Some template text

    {% url 'this-view-does-not-exist' %}

    Some other template text

The intention is to help catching typos and leftover references when you rename
or remove a named view - before real users hit the relevant templates.

Options
-------

ignore-apps
~~~~~~~~~~~

Ignore these apps (comma separated list) when looking for templates to check.
Default is "admin".

urlconf
~~~~~~~

Set the settings URL conf variable to use


Usage Example
-------------

::

    ./manage.py verify_named_urls

Example output, where the first named URL is defined, the second is missing:

::

    Name: entry-detail (1 occurences, handled in EntryDetailView, blog/<slug:slug>)
    * /home/myuser/django/blog/templates/blog/entry-list.html:9
    Name: this-view-is-removed-by-now (1 occurences, UNKNOWN VIEW)
    * /home/myuser/django/blog/templates/blog/reference.html:6
