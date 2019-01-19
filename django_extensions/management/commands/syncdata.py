# -*- coding: utf-8 -*-
"""
SyncData
========

Django command similar to 'loaddata' but also deletes.
After 'syncdata' has run, the database will have the same data as the fixture - anything
missing will of been added, anything different will of been updated,
and anything extra will of been deleted.
"""

import os

import six
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction
from django.template.defaultfilters import pluralize

from django_extensions.management.utils import signalcommand


class SyncDataError(Exception):
    pass


class Command(BaseCommand):
    """ syncdata command """

    help = 'Makes the current database have the same data as the fixture(s), no more, no less.'
    args = "fixture [fixture ...]"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--skip-remove', action='store_false',
                            dest='remove', default=True,
                            help='Avoid remove any object from db'),
        parser.add_argument('fixture_labels', nargs='?', type=str,
                            help='Specify the fixture label (comma separated)')

    def remove_objects_not_in(self, objects_to_keep, verbosity):
        """
        Deletes all the objects in the database that are not in objects_to_keep.
        - objects_to_keep: A map where the keys are classes, and the values are a
         set of the objects of that class we should keep.
        """
        for class_ in objects_to_keep.keys():
            current = class_.objects.all()
            current_ids = set([x.pk for x in current])
            keep_ids = set([x.pk for x in objects_to_keep[class_]])

            remove_these_ones = current_ids.difference(keep_ids)
            if remove_these_ones:
                for obj in current:
                    if obj.pk in remove_these_ones:
                        obj.delete()
                        if verbosity >= 2:
                            print("Deleted object: %s" % six.u(obj))

            if verbosity > 0 and remove_these_ones:
                num_deleted = len(remove_these_ones)
                if num_deleted > 1:
                    type_deleted = six.u(class_._meta.verbose_name_plural)
                else:
                    type_deleted = six.u(class_._meta.verbose_name)

                print("Deleted %s %s" % (str(num_deleted), type_deleted))

    @signalcommand
    def handle(self, *args, **options):
        self.style = no_style()
        fixture_labels = options['fixture_labels'].split(',') \
            if options['fixture_labels'] else ()
        try:
            with transaction.atomic():
                self.syncdata(fixture_labels, options)
        except SyncDataError as exc:
            print(self.style.ERROR(exc))

        # Close the DB connection. This is required as a workaround for an
        # edge case in MySQL: if the same connection is used to
        # create tables, load data, and query, the query can return
        # incorrect results. See Django #7572, MySQL #37735.
        connection.close()

    def syncdata(self, fixture_labels, options):
        """ Main method of a Django command """

        verbosity = options['verbosity']
        show_traceback = options['traceback']

        # Keep a count of the installed objects and fixtures
        fixture_count = 0
        object_count = 0
        objects_per_fixture = []
        models = set()

        humanize = lambda dirname: dirname and "'%s'" % dirname or 'absolute path'

        # Get a cursor (even though we don't need one yet). This has
        # the side effect of initializing the test database (if
        # it isn't already initialized).
        cursor = connection.cursor()

        app_modules = [app.module for app in apps.get_app_configs()]
        app_fixtures = [os.path.join(os.path.dirname(app.__file__), 'fixtures') for app in app_modules]
        for fixture_label in fixture_labels:
            parts = fixture_label.split('.')
            if len(parts) == 1:
                fixture_name = fixture_label
                formats = serializers.get_public_serializer_formats()
            else:
                fixture_name, format = '.'.join(parts[:-1]), parts[-1]
                if format in serializers.get_public_serializer_formats():
                    formats = [format]
                else:
                    formats = []

            if formats:
                if verbosity > 1:
                    print("Loading '%s' fixtures..." % fixture_name)
            else:
                raise SyncDataError("Problem installing fixture '%s': %s is not a known serialization format." % (fixture_name, format))

            if os.path.isabs(fixture_name):
                fixture_dirs = [fixture_name]
            else:
                fixture_dirs = app_fixtures + list(settings.FIXTURE_DIRS) + ['']

            for fixture_dir in fixture_dirs:
                if verbosity > 1:
                    print("Checking %s for fixtures..." % humanize(fixture_dir))

                label_found = False
                for format in formats:
                    if verbosity > 1:
                        print("Trying %s for %s fixture '%s'..." % (humanize(fixture_dir), format, fixture_name))
                    try:
                        full_path = os.path.join(fixture_dir, '.'.join([fixture_name, format]))
                        fixture = open(full_path, 'r')
                        if label_found:
                            fixture.close()
                            raise SyncDataError("Multiple fixtures named '%s' in %s. Aborting." % (fixture_name, humanize(fixture_dir)))
                        else:
                            fixture_count += 1
                            objects_per_fixture.append(0)
                            if verbosity > 0:
                                print("Installing %s fixture '%s' from %s." % (format, fixture_name, humanize(fixture_dir)))
                            try:
                                objects_to_keep = {}
                                objects = serializers.deserialize(format, fixture)
                                for obj in objects:
                                    object_count += 1
                                    objects_per_fixture[-1] += 1

                                    class_ = obj.object.__class__
                                    if class_ not in objects_to_keep:
                                        objects_to_keep[class_] = set()
                                    objects_to_keep[class_].add(obj.object)

                                    models.add(class_)
                                    obj.save()

                                if options['remove']:
                                    self.remove_objects_not_in(objects_to_keep, verbosity)

                                label_found = True
                            except (SystemExit, KeyboardInterrupt):
                                raise
                            except Exception:
                                import traceback
                                fixture.close()
                                transaction.rollback()
                                if show_traceback:
                                    traceback.print_exc()
                                raise SyncDataError("Problem installing fixture '%s': %s\n" % (full_path, traceback.format_exc()))

                            fixture.close()
                    except SyncDataError as e:
                        raise e
                    except Exception:
                        if verbosity > 1:
                            print("No %s fixture '%s' in %s." % (format, fixture_name, humanize(fixture_dir)))

        # If any of the fixtures we loaded contain 0 objects, assume that an
        # error was encountered during fixture loading.
        if 0 in objects_per_fixture:
            raise SyncDataError("No fixture data found for '%s'. (File format may be invalid.)" % fixture_name)

        # If we found even one object in a fixture, we need to reset the
        # database sequences.
        if object_count > 0:
            sequence_sql = connection.ops.sequence_reset_sql(self.style, models)
            if sequence_sql:
                if verbosity > 1:
                    print("Resetting sequences")
                for line in sequence_sql:
                    cursor.execute(line)

        if object_count == 0:
            if verbosity > 1:
                print("No fixtures found.")
        else:
            if verbosity > 0:
                print("Installed %d object%s from %d fixture%s" % (
                    object_count, pluralize(object_count),
                    fixture_count, pluralize(fixture_count)
                ))
