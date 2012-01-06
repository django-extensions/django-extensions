"""
Sync Media to S3
================

Django command that scans all files in your settings.MEDIA_ROOT folder and
uploads them to S3 with the same directory structure.

This command can optionally do the following but it is off by default:
* gzip compress any CSS and Javascript files it finds and adds the appropriate
  'Content-Encoding' header.
* set a far future 'Expires' header for optimal caching.

Note: This script requires the Python boto library and valid Amazon Web
Services API keys.

Required settings.py variables:
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_BUCKET_NAME = ''

Command options are:
  -p PREFIX, --prefix=PREFIX
                        The prefix to prepend to the path on S3.
  --gzip                Enables gzipping CSS and Javascript files.
  --expires             Enables setting a far future expires header.
  --force               Skip the file mtime check to force upload of all
                        files.
  --filter-list         Override default directory and file exclusion
                        filters. (enter as comma seperated line)

TODO:
 * Use fnmatch (or regex) to allow more complex FILTER_LIST rules.

"""
import datetime
import email
import mimetypes
import optparse
import os
import sys
import time
import threading
from Queue import Queue, Empty

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Make sure boto is available
try:
    import boto
    import boto.exception
except ImportError:
    raise ImportError, "The boto Python library is not installed."


class Command(BaseCommand):
    # Extra variables to avoid passing these around
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    AWS_BUCKET_NAME = ''
    DIRECTORY = ''
    FILTER_LIST = ['.DS_Store', '.svn', '.hg', '.git', 'Thumbs.db']
    GZIP_CONTENT_TYPES = (
        'text/css',
        'application/javascript',
        'application/x-javascript',
        'text/javascript'
    )

    upload_count = 0
    skip_count = 0

    option_list = BaseCommand.option_list + (
        optparse.make_option('-p', '--prefix',
            dest='prefix',
            default=getattr(settings, 'SYNC_MEDIA_S3_PREFIX', ''),
            help="The prefix to prepend to the path on S3."),
        optparse.make_option('-d', '--dir',
            dest='dir', default=settings.MEDIA_ROOT,
            help="The root directory to use instead of your MEDIA_ROOT"),
        optparse.make_option('--gzip',
            action='store_true', dest='gzip', default=False,
            help="Enables gzipping CSS and Javascript files."),
        optparse.make_option('--expires',
            action='store_true', dest='expires', default=False,
            help="Enables setting a far future expires header."),
        optparse.make_option('--force',
            action='store_true', dest='force', default=False,
            help="Skip the file mtime check to force upload of all files."),
        optparse.make_option('--filter-list', dest='filter_list',
            action='store', default='',
            help="Override default directory and file exclusion filters. (enter as comma seperated line)"),
        optparse.make_option('-t', '--threads', dest='num_threads',
            action='store', default=5,
            help="The number of threads to use while uploading"),
    )

    help = 'Syncs the complete MEDIA_ROOT structure and files to S3 into the given bucket name.'
    args = 'bucket_name'

    can_import_settings = True

    def handle(self, *args, **options):

        # Check for AWS keys in settings
        if not hasattr(settings, 'AWS_ACCESS_KEY_ID') or \
            not hasattr(settings, 'AWS_SECRET_ACCESS_KEY'):
            raise CommandError('Missing AWS keys from settings file.  Please' +
                                'supply both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.')
        else:
            self.AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
            self.AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

        if not hasattr(settings, 'AWS_BUCKET_NAME'):
            raise CommandError('Missing bucket name from settings file. Please' +
                ' add the AWS_BUCKET_NAME to your settings file.')
        else:
            if not settings.AWS_BUCKET_NAME:
                raise CommandError('AWS_BUCKET_NAME cannot be empty.')
        self.AWS_BUCKET_NAME = settings.AWS_BUCKET_NAME

        if not hasattr(settings, 'MEDIA_ROOT'):
            raise CommandError('MEDIA_ROOT must be set in your settings.')
        else:
            if not settings.MEDIA_ROOT:
                raise CommandError('MEDIA_ROOT must be set in your settings.')

        self.verbosity = int(options.get('verbosity'))
        self.prefix = options.get('prefix')
        self.do_gzip = options.get('gzip')
        self.do_expires = options.get('expires')
        self.do_force = options.get('force')
        self.num_threads = int(options.get('num_threads'))
        self.DIRECTORY = options.get('dir')
        self.FILTER_LIST = getattr(settings, 'FILTER_LIST', self.FILTER_LIST)
        filter_list = options.get('filter_list')
        if filter_list:
            # command line option overrides default filter_list and
            # settings.filter_list
            self.FILTER_LIST = filter_list.split(',')

        # Now call the syncing method to walk the MEDIA_ROOT directory and
        # upload all files found.
        self.sync_s3()

        print
        print "%d files uploaded." % (self.upload_count)
        print "%d files skipped." % (self.skip_count)

    def sync_s3(self):
        """
        Walks the media directory and syncs files to S3
        """
        # queue to check for what files to upload
        self.file_queue = Queue()
        # queue of files to upload to s3
        self.upload_queue = Queue()

        os.path.walk(self.DIRECTORY, self.check_media_dir,
            (self.AWS_BUCKET_NAME, self.DIRECTORY))

        if self.verbosity > 0:
            print "Checking %d files..." % self.file_queue.qsize()
        self.start_filecheck_threads()
        if self.verbosity > 0:
            print "Uploading %d new files..." % self.upload_queue.qsize()
        self.start_upload_threads()

    def compress_string(self, s):
        """Gzip a given string."""
        import gzip
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        zbuf = StringIO()
        zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
        zfile.write(s)
        zfile.close()
        return zbuf.getvalue()

    def open_s3(self):
        """
        Opens connection to S3 returning bucket and key
        """
        conn = boto.connect_s3(self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
        try:
            bucket = conn.get_bucket(self.AWS_BUCKET_NAME)
        except boto.exception.S3ResponseError:
            bucket = conn.create_bucket(self.AWS_BUCKET_NAME)
        return bucket, boto.s3.key.Key(bucket)

    def check_media_dir(self, arg, dirname, names):
        """
        This is the callback to os.path.walk and where much of the work happens
        """
        bucket_name, root_dir = arg

        # Skip directories we don't want to sync
        if os.path.basename(dirname) in self.FILTER_LIST:
            # prevent walk from processing subfiles/subdirs below the ignored one
            del names[:]
            return

        # Later we assume the MEDIA_ROOT ends with a trailing slash
        if not root_dir.endswith(os.path.sep):
            root_dir = root_dir + os.path.sep

        for file in names:
            file_obj = {}
            file_obj['file'] = file
            file_obj['dirname'] = dirname
            file_obj['root_dir'] = root_dir
            self.file_queue.put(file_obj)

    def should_upload(self, file, bucket, key):
        """
        Checks if a file on the local file system should be uploaded to
        S3 by comparing the last modified timestamps.
        """
        headers = {}
        queue_obj = {}

        if file['file'] in self.FILTER_LIST:
            return # Skip files we don't want to sync

        filename = os.path.join(file['dirname'], file['file'])
        if os.path.isdir(filename):
            return # Don't try to upload directories

        file_key = filename[len(file['root_dir']):]
        if self.prefix:
            file_key = '%s/%s' % (self.prefix, file_key)

        # Check if file on S3 is older than local file, if so, upload
        if not self.do_force:
            s3_key = bucket.get_key(file_key)
            if s3_key:
                s3_datetime = datetime.datetime(*time.strptime(
                    s3_key.last_modified, '%a, %d %b %Y %H:%M:%S %Z')[0:6])
                local_datetime = datetime.datetime.utcfromtimestamp(
                    os.stat(filename).st_mtime)
                if local_datetime < s3_datetime:
                    self.skip_count += 1
                    if self.verbosity > 1:
                        print "File %s hasn't been modified since last " \
                            "being uploaded" % (file_key)
                    return

        queue_obj['filename'] = filename
        queue_obj['headers'] = headers
        queue_obj['file_key'] = file_key

        # File is newer, let's process and upload
        self.upload_queue.put(queue_obj)

    def file_worker(self):
        """
        Worker thread to process the file check queue.
        """
        bucket, key = self.open_s3()
        while True:
            try:
                item = self.file_queue.get(False)
            except Empty:
                return
            else:
                try:
                    self.should_upload(item, bucket, key)
                    self.file_queue.task_done()
                except:
                    # so this thread doesn't stall
                    self.file_queue.task_done()

    def start_filecheck_threads(self):
        """
        Starts thread to check list of files that needs to be uploaded.
        """
        for i in range(self.num_threads):
            consumer = threading.Thread(target=self.file_worker)
            consumer.start()

        # block until queue is done
        self.file_queue.join()


    def upload_worker(self):
        """
        Worker thread to upload files to s3.
        """
        bucket, key = self.open_s3()
        while True:
            try:
                item = self.upload_queue.get(False)
            except Empty:
                return
            else:
                try:
                    self.upload_s3(item, bucket, key)
                    self.upload_queue.task_done()
                except:
                    # so this thread doesn't stall
                    self.upload_queue.task_done()
                    return

    def start_upload_threads(self):
        """
        Starts upload threads.
        """
        for i in range(self.num_threads):
            consumer = threading.Thread(target=self.upload_worker)
            consumer.start()

        self.upload_queue.join()

    def upload_s3(self, upload, bucket, key):
        """
        Performs upload to s3.
        """

        if self.verbosity > 0:
            print "Uploading %s..." % (upload['file_key'])

        content_type = mimetypes.guess_type(upload['filename'])[0]
        if content_type:
            upload['headers']['Content-Type'] = content_type
        file_obj = open(upload['filename'], 'rb')
        file_size = os.fstat(file_obj.fileno()).st_size
        filedata = file_obj.read()
        if self.do_gzip:
            # Gzipping only if file is large enough (>1K is recommended)
            # and only if file is a common text type (not a binary file)
            if file_size > 1024 and content_type in self.GZIP_CONTENT_TYPES:
                filedata = self.compress_string(filedata)
                upload['headers']['Content-Encoding'] = 'gzip'
                if self.verbosity > 1:
                    print "\tgzipped: %dk to %dk" % \
                        (file_size / 1024, len(filedata) / 1024)
        if self.do_expires:
            # HTTP/1.0
            upload['headers']['Expires'] = '%s GMT' % (email.Utils.formatdate(
                time.mktime((datetime.datetime.now() +
                datetime.timedelta(days=365 * 2)).timetuple())))
            # HTTP/1.1
            upload['headers']['Cache-Control'] = 'max-age %d' % (3600 * 24 * 365 * 2)
            if self.verbosity > 1:
                print "\texpires: %s" % (upload['headers']['Expires'])
                print "\tcache-control: %s" % (upload['headers']['Cache-Control'])

        try:
            key.name = upload['file_key']
            key.set_contents_from_string(filedata, upload['headers'], replace=True)
            key.set_acl('public-read')
        except boto.exception.S3CreateError, e:
            print "Failed: %s" % e
        except Exception, e:
            print e
            print "Error uploading %s" % upload['file_key']
            raise
        else:
            self.upload_count += 1

        file_obj.close()

# Backwards compatibility for Django r9110
if not [opt for opt in Command.option_list if opt.dest == 'verbosity']:
    Command.option_list += (
        optparse.make_option('-v', '--verbosity',
            dest='verbosity', default=1, action='count',
            help="Verbose mode. Multiple -v options increase the verbosity."),
    )
