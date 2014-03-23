Namespace proposal
==================

:synopsis: Namespace Proposal


Introduction
------------

Please change / write your proposal for splitting django_extensions into
namespaces here.


Proposal of a Namespace
-----------------------

Rough proposal for splitting into functional parts:

* django_extensions.commands (20% that everbody uses / production)
* django_extensions.commands.development (everything development)
* django_extensions.commands.extra (not fitting about category's?)
* django_extensions.db
* django_extensions.templates
* django_extensions.jobs

The db part should be okay where it is right now. It's only used when
somebody explicitly imports::

  from django_extensions.db.models import something
