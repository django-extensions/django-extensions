# coding: utf-8

from __future__ import unicode_literals, division, print_function
import csv
import os
import sys
from time import time

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import connection
from django.db.models import FileField
from django.db.models.loading import get_models
from django.utils.six import PY3

from django_extensions.management.utils import signalcommand


if PY3:
    raw_input = input


def si_prefix(num, suffix='B'):
    """
    Converts a number into a SI (« Système International ») prefixed string.
    """
    for unit in ('', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'):
        if num < 1000:
            break
        num /= 1000
    return '%.2f %s%s' % (num, unit, suffix)


class Command(NoArgsCommand):
    help = 'Collects unregistered media files in a CSV ' \
           'and deletes them if you confirm it.'

    REFRESH_RATE = 0.5  # seconds
    CSV_PATH = 'unregistered_files.csv'
    UNDETECTABLE_FILE_FIELDS = {
        'easy_thumbnails': (('easy_thumbnails_thumbnail', 'name'),)
    }

    @signalcommand
    def handle_noargs(self, **options):
        print('Finding unregistered media...')
        print('(You will be asked to confirm deletion after that)')
        unregistered_media_count = self.find_unregistered_media()

        if unregistered_media_count:
            self.ask_for_deletion()
        else:
            print('All media are well registered; nothing to delete.')

    def get_file_columns(self):
        file_fields = set()

        for app, tables_and_columns in self.UNDETECTABLE_FILE_FIELDS.items():
            if app in settings.INSTALLED_APPS:
                file_fields.update(tables_and_columns)

        for model in get_models():
            file_fields.update([
                (f.model._meta.db_table, f.get_attname_column()[1])
                for f in model._meta.fields if isinstance(f, FileField)])

        return file_fields

    def get_file_registered_sql(self):
        sql = ''
        table_and_columns = self.get_file_columns()
        for db_table, db_column in table_and_columns:
            if sql:
                sql += ' UNION '
            sql += '(SELECT 1 FROM %s WHERE %s = %%s)' % (db_table, db_column)
        return sql, len(table_and_columns)

    def delete_files(self):
        print('Deleting files...')
        with open(self.CSV_PATH) as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                os.remove(row['path'])
        print('Unregistered media files successfully deleted.')

    def ask_for_deletion(self):
        print('\n'
              'Be careful!\n'
              'This script only inspects database fields defined\n'
              'using FileField or ImageField in Django.\n'
              'If you stored media paths in a CharField or a TextField,\n'
              'the corresponding files are marked for destruction!'
              '\n')
        print('Check what will be deleted by opening '
              'the generated CSV file "%s".' % self.CSV_PATH)
        print('To exclude some files from deletion, edit this CSV now\n'
              'and remove lines mentioning files you want to keep.')
        user_choice = raw_input(
            'Delete media files mentioned in that CSV? [yN] ')
        if user_choice in ('y', 'yes', 'Y'):
            self.delete_files()
        else:
            print('Canceled.')

    @staticmethod
    def media_iterator():
        for abs_root, _, filenames in os.walk(settings.MEDIA_ROOT):
            rel_root = os.path.relpath(abs_root, settings.MEDIA_ROOT)
            for filename in filenames:
                abs_path = os.path.join(abs_root, filename)
                rel_path = os.path.join(rel_root, filename)
                yield abs_path, rel_path

    def find_unregistered_media(self):
        sql, n_params = self.get_file_registered_sql()
        media_count = 0
        unregistered_media_count = 0
        media_size = 0
        unregistered_media_size = 0
        previous_time = time()
        cursor = connection.cursor()

        with open(self.CSV_PATH, 'w') as f:
            csv_writer = csv.DictWriter(f, fieldnames=('path', 'size'))
            csv_writer.writeheader()

            for abs_path, rel_path in self.media_iterator():
                cursor.execute(sql, params=[rel_path] * n_params)
                media_count += 1
                file_size = os.stat(abs_path).st_size
                media_size += file_size
                is_registered = cursor.fetchone()
                if is_registered is None:
                    unregistered_media_count += 1
                    unregistered_media_size += file_size
                    csv_writer.writerow({'path': abs_path, 'size': file_size})

                if time() - previous_time > self.REFRESH_RATE:
                    sys.stdout.write(
                        '\r%9s / %-9s (%3d%% of %d files) of media '
                        'are not registered in database.'
                        % (si_prefix(unregistered_media_size),
                           si_prefix(media_size),
                           (100 * unregistered_media_count) // media_count,
                           media_count))
                    sys.stdout.flush()
                    previous_time = time()

        print()  # Prints a newline because we didn’t do it above.
        cursor.close()

        return unregistered_media_count
