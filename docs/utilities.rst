Utilities
=========

:synopsis: Other utility functions or classes


InternalIPS
-----------

`InternalIPS` allows to specify CIDRs for `INTERNAL_IPS` settings parameter.

Example `settings.py`::

  from django_extensions.utils import InternalIPS

  INTERNAL_IPS = InternalIPS([
      "127.0.0.1",
      "172.16.0.0/16",
  ])

Use `sort_by_size` to sort the lookups to search the largest subnet first.

Example `settings.py`::

  from django_extensions.utils.internal_ips import InternalIPS

  INTERNAL_IPS = InternalIPS([
      "127.0.0.1",
      "172.16.0.0/16",
  ], sort_by_size=True)

`InternalIPS` is inspired by `netaddr.IPSet` please consider using it instead as
it is more optimized but requires the additional `netaddr` package.
