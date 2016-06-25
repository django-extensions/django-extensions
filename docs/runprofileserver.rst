RunProfileServer
================

*We recommend that before you start profiling any language or
framework you learn enough about it so that you feel comfortable with digging
into its internals.*

*Without sufficient knowledge it will not only be (very)
hard but you're likely to make wrong assumptions (and fixes). As a rule of thumb,
clean, well written code will help you a lot more than overzealous
micro-optimizations will.*

*This document is work in progress. If you feel you can help with
better/clearer or additional information about profiling Django please leave a
comment.*


Introduction
------------

*runprofileserver* starts Django's runserver command with hotshot/profiling
tools enabled. It will save .prof files containing the profiling information
into the --prof-path directory. Note that for each request made one profile
data file is saved.

By default the profile-data-files are saved in /tmp use the --prof-path option
to specify your own target directory. Saving the data in a meaningful directory
structure helps to keep your profile data organized and keeps /tmp uncluttered.
(Yes this probably malfunctions systems such as Windows where /tmp does not exist)

To define profile filenames use --prof-file option. Default format
is "{path}.{duration:06d}ms.{time}" (Python
`Format Specification <http://docs.python.org/3/library/string.html#formatspec>`_
is used).

Examples:

  * "{time}-{path}-{duration}ms" - to order profile-data-files by request time
  * "{duration:06d}ms.{path}.{time}" - to order by request duration

gather_profile_stats.py
-----------------------

Django comes packed with a tool to aggregate these different prof files into
one aggregated profile file. This tool is called *gather_profile_stats.py* and
is located inside the *bin* directory of your Django distribution.


Profiler choice
---------------
*runprofileserver* supports two profilers: *hotshot* and *cProfile*. Both come
with the standard Python library but *cProfile* is more recent and may not be
available on all systems. For this reason, *hotshot* is the default profiler.

However, *hotshot* `is not maintained anymore <https://docs.python.org/2/library/profile.html#introduction-to-the-profilers>`_
and using *cProfile* is usually the recommended way.
If it is available on your system, you can use it with the option ``--use-cprofile``.

Example::

  $ mkdir /tmp/my-profile-data
  $ ./manage.py runprofileserver --use-cprofile --prof-path=/tmp/my-profile-data

If you used the default profiler but are not able to open the profiling results
with the ``pstats`` module or with your profiling GUI of choice because of an
error "*ValueError: bad marshal data (unknown type code)*", try using *cProfile*
instead.

KCacheGrind
-----------

Recent versions of *runprofileserver* have an option to save the profile data
into a KCacheGrind compatible format. So you can use the excellent KCacheGrind
tool for analyzing the profile data.

Example::

  $ mkdir /tmp/my-profile-data
  $ ./manage.py runprofileserver --kcachegrind --prof-path=/tmp/my-profile-data
  Validating models...
  0 errors found

  Django version X.Y.Z, using settings 'complete_project.settings'
  Development server is running at http://127.0.0.1:8000/
  Quit the server with CONTROL-C.
  [13/Nov/2008 06:29:38] "GET / HTTP/1.1" 200 41107
  [13/Nov/2008 06:29:39] "GET /site_media/base.css?743 HTTP/1.1" 200 17227
  [13/Nov/2008 06:29:39] "GET /site_media/logo.png HTTP/1.1" 200 3474
  [13/Nov/2008 06:29:39] "GET /site_media/jquery.js HTTP/1.1" 200 31033
  [13/Nov/2008 06:29:39] "GET /site_media/heading.png HTTP/1.1" 200 247
  [13/Nov/2008 06:29:39] "GET /site_media/base.js HTTP/1.1" 200 751
  <ctrl-c>
  $ kcachegrind /tmp/my-profile-data/root.12574391.592.prof

Here is a screenshot of how the above commands might look in KCacheGrind:

  http://trbs.net/media/misc/django-runprofileserver-kcachegrind-full.jpg

Links
-----

* http://code.djangoproject.com/wiki/ProfilingDjango
* http://www.rkblog.rk.edu.pl/w/p/django-profiling-hotshot-and-kcachegrind/
* http://code.djangoproject.com/browser/django/trunk/django/bin/profiling/gather_profile_stats.py
* http://www.oluyede.org/blog/2007/03/07/profiling-django/
* http://simonwillison.net/2008/May/22/debugging/
