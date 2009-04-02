dumpscript
==========

:synopsis: Generates a standalone Python script that will repopulate the database using objects.

The `dumpscript` command generates a standalone Python script that will
repopulate the database using objects. The advantage of this approach is that
it is easy to understand, and more flexible than directly populating the
database, or using XML.

Why?
----

There are a few benefits to this:

* less drama with model evolution: foreign keys handled naturally without IDs,
  new and removed columns are ignored
* edit script to create 1,000s of generated entries using for loops, generated
  names, python modules etc.

For example, an edited script can populate the database with test data::

  for i in xrange(2000):
      poll = Poll()
      poll.question = "Question #%d" % i
      poll.pub_date = date(2001,01,01) + timedelta(days=i)
      poll.save()

Real databases will probably be bigger and more complicated, and so it is useful
to enter some values using the admin interface and then edit the generated
scripts.


Features
--------

* *ForeignKey* and *ManyToManyFields* (using python variables, not object IDs)
* Self-referencing *ForeignKey* (and M2M) fields
* Sub-classed models
* *ContentType* fields and generic relationships (but see issue 43)
* Recursive references
* *AutoFields* are excluded
* Parent models are only included when no other child model links to it
* Individual models can be referenced


What it can't do (yet!)
-----------------------

* Ideal handling of generic relationships (ie no *AutoField* references):
  issue 43
* Intermediate join tables: issue 48
* GIS fields: issue 72


How?
----

To dump the data from all the models in a given Django app (`appname`)::

  $ ./manage.py dumpscript appname > scripts/testdata.py

To dump the data from just a single model (`appname.ModelName`)::

  $ ./manage.py dumpscript appname.ModelName > scripts/testdata.py

To reset a given app, and reload with the saved data::

  $ ./manage.py reset appname
  $ ./manage.py runscript testdata

Note: Runscript needs *scripts* to be a module, so create the directory and a
*__init__.py* file.
