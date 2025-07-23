# -*- coding: utf-8 -*-
"""
Sync Media to S3
================

Django command that scans all files in your settings.MEDIA_ROOT and
settings.STATIC_ROOT folders and uploads them to S3 with the same directory
structure.

This command can optionally do the following but it is off by default:
* gzip compress any CSS and Javascript files it finds and adds the appropriate
  'Content-Encoding' header.
* set a far future 'Expires' header for optimal caching.
* upload only media or static files.
* use any other provider compatible with Amazon S3.
* set other than 'public-read' ACL.

Note: This script requires the Python boto library and valid Amazon Web
Services API keys.

Required settings.py variables:
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_BUCKET_NAME = ''

When you call this command with the `--renamegzip` param, it will add
the '.gz' extension to the file name. But Safari just doesn't recognize
'.gz' files and your site won't work on it! To fix this problem, you can
set any other extension (like .jgz) in the `SYNC_S3_RENAME_GZIP_EXT`
variable.

Command options are:
  -p PREFIX, --prefix=PREFIX
                        The prefix to prepend to the path on S3.
  --gzip                Enables gzipping CSS and Javascript files.
  --expires             Enables setting a far future expires header.
  --force               Skip the file mtime check to force upload of all
                        files.
  --filter-list         Override default directory and file exclusion
                        filters. (enter as comma separated line)
  --renamegzip          Enables renaming of gzipped files by appending '.gz'.
                        to the original file name. This way your original
                        assets will not be replaced by the gzipped ones.
                        You can change the extension setting the
                        `SYNC_S3_RENAME_GZIP_EXT` var in your settings.py
                        file.
  --invalidate          Invalidates the objects in CloudFront after uploading
                        stuff to s3.
  --media-only          Only MEDIA_ROOT files will be uploaded to S3.
  --static-only         Only STATIC_ROOT files will be uploaded to S3.
  --s3host              Override default s3 host.
  --acl                 Override default ACL settings ('public-read' if
                        settings.AWS_DEFAULT_ACL is not defined).

TODO:
 * Use fnmatch (or regex) to allow more complex FILTER_LIST rules.

"""
import email
import gzip
import mimetypes
import os
import pathlib
import time
from io import BytesIO

import boto3
import boto3.exceptions
from boto3.s3 import transfer
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand

try:
    import boto3
except ImportError:
    HAS_BOTO = False
else:
    HAS_BOTO = True


class Command(BaseCommand):
    AWS_S3_ACCESS_KEY_ID = None
    AWS_S3_SECRET_ACCESS_KEY = None
    AWS_STORAGE_BUCKET_NAME = None
    AWS_S3_REGION_NAME = None
    AWS_CLOUDFRONT_DISTRIBUTION = None

    SYNC_S3_RENAME_GZIP_EXT = ''

    GZIP_CONTENT_TYPES = (
        "text/css",
        "application/javascript",
        "application/x-javascript",
        "text/javascript",
    )

    help = (
        "Syncs the complete MEDIA_ROOT structure "
        "and files to S3 into the given bucket name"
    )
    # args = 'bucket_name'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.directories = []
        self.media_only = False
        self.static_only = False
        self.filter_list = []
        self.prefix = None
        self.force_upload = False
        self.verbosity = False
        self.gzip = False
        self.expires = False
        self.upload_count = 0
        self.uploaded_files = []
        self.request_cloudfront_invalidation = False
        self.default_acl = None
        self.using_dir = None

    @signalcommand
    def handle(self, *args, **options):
        self.AWS_S3_ACCESS_KEY_ID = getattr(
            settings,
            'AWS_S3_ACCESS_KEY_ID',
            None
        )
        self.AWS_S3_SECRET_ACCESS_KEY = getattr(
            settings,
            'AWS_S3_SECRET_ACCESS_KEY',
            None
        )
        self.AWS_STORAGE_BUCKET_NAME = getattr(
            settings,
            'AWS_STORAGE_BUCKET_NAME',
            None
        )
        self.AWS_S3_REGION_NAME = getattr(
            settings,
            'AWS_S3_REGION_NAME',
            None
        )
        self.AWS_CLOUDFRONT_DISTRIBUTION = getattr(
            settings,
            'AWS_CLOUDFRONT_DISTRIBUTION',
            None
        )

        self.SYNC_S3_RENAME_GZIP_EXT = getattr(
            settings,
            'SYNC_S3_RENAME_GZIP_EXT',
            None
        )

        has_access_keys = all([
            self.AWS_S3_ACCESS_KEY_ID is not None,
            self.AWS_S3_SECRET_ACCESS_KEY is not None
        ])

        if not has_access_keys:
            raise CommandError(
                'Missing AWS_S3_ACCESS_KEY_ID and/or '
                'AWS_S3_SECRET_ACCESS_KEY in the settings file'
            )

        if not self.AWS_STORAGE_BUCKET_NAME:
            raise CommandError(
                'Missing AWS_STORAGE_BUCKET_NAME '
                'in the settings file'
            )

        if not getattr(settings, 'MEDIA_ROOT'):
            raise CommandError(
                'MEDIA_ROOT should be set '
                'in your settings file'
            )

        if self.media_only and self.static_only:
            raise ValueError(
                'static_only and media_only '
                'cannot be used at the same time'
            )

        if self.media_only:
            self.directories = [settings.MEDIA_ROOT]
        elif self.static_only:
            self.directories = [settings.STATIC_ROOT]
        else:
            self.directories = [settings.MEDIA_ROOT, settings.STATIC_ROOT]

        # TODO: Seems like the logic is to override
        # all the dirs when this is set
        self.using_dir = options['using_dir']
        if self.using_dir:
            self.directories.append(self.using_dir)

        self.prefix = options['prefix']
        self.default_acl = options['acl']
        self.force_upload = options['force_upload']
        self.media_only = options['media_only']
        self.static_only = options['static_only']
        self.verbosity = options['verbosity']
        self.gzip = options['gzip']
        self.expires = options['expires']
        self.renamegzip = options['renamegzip']
        self.s3host = options['s3host']

        filter_list_from_settings = getattr(settings, 'AWS_S3_FILTER_LIST', [])

        filter_list_from_cmd = options['filter_list']
        filter_list_from_cmd = filter_list_from_cmd.split(',')

        self.filter_list.extend(
            filter_list_from_cmd + filter_list_from_settings
        )

        self._walk_folders()

        if self.request_cloudfront_invalidation:
            self._call_cloudfront_invalidation()

    def _create_s3_connection(self):
        """Creates a new connection to S3"""
        session = boto3.Session(**{
            'aws_access_key_id': self.AWS_S3_ACCESS_KEY_ID,
            'aws_secret_access_key': self.AWS_S3_SECRET_ACCESS_KEY,
            'region_name': self.AWS_S3_REGION_NAME
        })

        client = session.client('s3')
        resource = session.resource('s3')
        bucket = resource.Bucket(self.AWS_STORAGE_BUCKET_NAME)
        if bucket is None:
            bucket = client.create_bucket(Bucket=self.AWS_STORAGE_BUCKET_NAME)
        return client, bucket

    def _create_cloudfront_connection(self):
        return boto3.client('cloudfront')

    def _handle_upload(self, root, dirs, files, **params):
        """Function that uploads the directory and files to S3"""
        client = params.get('client')
        bucket = params.get('bucket')
        bucket_key = params.get('bucket_key')

        root = pathlib.Path(root)
        if root.name in self.filter_list:
            return

        # The main directory in which the file is located:
        # e.g. media/, static/
        directory = pathlib.Path(params.get('directory', ''))

        if str(directory).endswith(os.path.sep):
            directory = directory.joinpath(os.path.sep)

        extra_args = {'ContentType': 'application/octet-stream'}
        extra_args.update(
            **{
                'ACL': 'public-read'
            }
        )

        for filename in files:
            if filename in self.filter_list:
                continue

            # The full path to the file to upload
            # the actual key will be determined below
            fullpath = root.joinpath(filename)
            if fullpath.is_dir():
                continue

            # Checks if the file on S3 is older
            # than the local files and if so uploads
            # it to the bucket
            if self.force_upload:
                pass

            if self.verbosity > 1:
                print(f'Uploading {filename}')

            content_type = mimetypes.guess_type(filename)[0]
            if content_type:
                extra_args.update(**{'ContentType': content_type})

            with open(fullpath, mode='rb') as f:
                file_size = os.fstat(f.fileno()).st_size
                file_data = f.read()

                # Get the parts of the path to the file
                # and create a relative path to the file
                # e.g. media/2010/01/01/file.txt
                parts = list(root.parts)[
                    list(root.parts).index(directory.name):]
                relative_path = '/'.join(parts)

                # This creates the final key or path that
                # will be used to save the file in s3
                file_key = f'{relative_path}/{filename}'

                # The files can be prefixed under a specific
                # main directory for organization
                if self.prefix:
                    file_key = f'{self.prefix}/{file_key}'

                if self.gzip:
                    # Gzip only if file is large enough (>1K is recommended)
                    # and only if file is a common text type (not a binary file)
                    file_constraints = all([
                        file_size > 1024,
                        content_type in self.GZIP_CONTENT_TYPES
                    ])

                    if file_constraints:
                        file_data = self._compress_string(file_data)
                        if self.renamegzip:
                            # If rename_gzip is True, then rename the file
                            # by appending an extension (like '.gz)' to
                            # original filename
                            file_key = f'{file_key}.{self.SYNC_S3_RENAME_GZIP_EXT}'

                    extra_args["ContentEncoding"] = 'gzip'

                    if self.verbosity > 1:
                        print(
                            f"Gzipped file: {file_size / 1024} "
                            f"to {file_data / 1024}"
                        )

                if self.expires:
                    time_value = time.mktime(
                        (
                            datetime.datetime.now() +
                            datetime.timedelta(days=365 * 2)
                        ).timetuple()
                    )

                    # HTTP/1.0
                    email.utils.formatdate(time_value)
                    extra_args['Expires'] = f'{time_value} GMT'

                    # HTTP/1.1
                    extra_args['CacheControl'] = f'max-age {3600 * 24 * 365 * 2}'

                    if self.verbosity > 1:
                        print(f"Expires: {extra_args['expires']}")
                        print(f"Cache control: {extra_args['Cache-Control']}")

                try:
                    instance = transfer.S3Transfer(client=client)
                    instance.upload_file(**{
                        'filename': str(fullpath),
                        'bucket': self.AWS_STORAGE_BUCKET_NAME,
                        'key': file_key,
                        'extra_args': extra_args
                    })
                except boto3.exceptions.S3TransferFailedError as e:
                    print('Failed')
                except Exception as e:
                    print(e)
                    raise
                else:
                    self.upload_count += 1
                    self.uploaded_files.append(fullpath)

    def _walk_folders(self):
        """Method used to walk the static and media folders
        in order to discover the files that should be uploaded
        to S3"""
        client, bucket = self._create_s3_connection()

        params = {
            'client': client,
            'bucket': bucket,
            'bucket_key': None,
            'directory': None
        }

        for directory in self.directories:
            # There can be a case where the user
            # for example does not set static root
            # for example and the directory is then None
            if directory is None:
                continue

            params['directory'] = directory
            for root, dirs, files in os.walk(directory):
                self._handle_upload(root, dirs, files, **params)

    def _call_cloudfront_invalidation(self):
        pass

    def _compress_string(self, content):
        """Helper function that Gzips a given
        string by doing xyz"""
        buffer = BytesIO()
        gzip_file = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=buffer)
        gzip_file.write(content)
        buffer.seek(0)
        gzip_file.close()
        return buffer.getvalue()

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '-p',
            '--prefix',
            dest='prefix',
            default=getattr(settings, 'SYNC_S3_PREFIX', ''),
            help="The prefix to prepend to the path on S3"
        )
        parser.add_argument(
            '-u',
            '--using-dir',
            dest='using_dir',
            help="Points to a custom static directory"
        )
        parser.add_argument(
            '--acl',
            dest='acl',
            default=getattr(settings, 'AWS_DEFAULT_ACL', 'public-read'),
            help="Overrides the default public-read ACL for the given file"
        )
        parser.add_argument(
            '--media-only',
            dest='media_only',
            default='',
            action='store_true',
            help="Uploads the content of the MEDIA_ROOT file onlye to s3"
        )
        parser.add_argument(
            '--static-only',
            dest='static_only',
            default='',
            action='store_true',
            help="Uploads the content of the STATIC_ROOT file only to s3"
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force_upload',
            default=False,
            help="Skip the file mtime check to force upload of all files."
        )
        parser.add_argument(
            '--filter-list',
            dest='filter_list',
            action='store',
            default='',
            help="Override default directory and file exclusion filters. (enter as comma seperated line)"
        )
        parser.add_argument(
            '-d',
            '--dir',
            dest='dir',
            help="Custom static root directory to use"
        )
        parser.add_argument(
            "--gzip",
            action="store_true",
            dest="gzip",
            default=False,
            help="Enables gzipping CSS and Javascript files.",
        )
        parser.add_argument(
            '--renamegzip',
            action='store_true',
            dest='renamegzip',
            default=False,
            help=(
                "'Enables renaming of gzipped assets to have '.gz' "
                "appended to the filename."
            ),
        )
        parser.add_argument(
            '--expires',
            action='store_true',
            dest='expires',
            default=False,
            help="Enables setting a far future expires header",
        )
        parser.add_argument(
            '--s3host',
            dest='s3host',
            default=getattr(settings, 'AWS_S3_HOST', ''),
            help="The s3 host (enables connecting to other providers/regions)"
        )
