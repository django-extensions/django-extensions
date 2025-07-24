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
AWS_S3_ACCESS_KEY_ID = ''
AWS_S3_SECRET_ACCESS_KEY = ''
AWS_STORAGE_BUCKET_NAME = ''

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
  --dry-run             Shows what would be uploaded without actually uploading it.

TODO:
 * Use fnmatch (or regex) to allow more complex FILTER_LIST rules.

"""
import datetime
import email
import gzip
import mimetypes
import os
import pathlib
import time
from io import BytesIO

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html

try:
    import boto3
    import boto3.exceptions
    from boto3.s3 import transfer
    from botocore.exceptions import (BotoCoreError, ClientError,
                                     NoCredentialsError)
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

        self.directories = []  # type: list[str]
        self.media_only = False
        self.static_only = False
        self.filter_list = []  # type: list[str]
        self.prefix = None
        self.force_upload = False
        self.verbosity = False
        self.gzip = False
        self.expires = False
        self.skip_count = 0
        self.upload_count = 0
        self.uploaded_files = []  # type: list[str]
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
            '.gz'
        )

        has_access_keys = all([
            self.AWS_S3_ACCESS_KEY_ID is not None,
            self.AWS_S3_SECRET_ACCESS_KEY is not None
        ])

        if not HAS_BOTO:
            raise CommandError(
                "Please install the 'boto3' Python library. ($ pip install boto3)"
            )

        if not has_access_keys:
            raise CommandError(
                'Missing AWS_S3_ACCESS_KEY_ID and/or '
                'AWS_S3_SECRET_ACCESS_KEY in your settings file'
            )

        if not self.AWS_STORAGE_BUCKET_NAME:
            raise CommandError(
                'Missing AWS_STORAGE_BUCKET_NAME '
                'in your settings file'
            )

        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            raise CommandError(
                'MEDIA_ROOT should be set '
                'in your settings file'
            )

        self.media_only = options['media_only']
        self.static_only = options['static_only']

        if self.media_only and self.static_only:
            raise CommandError(
                '--static-only and --media-only options '
                'cannot be used together'
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
        self.verbosity = options['verbosity']
        self.gzip = options['gzip']
        self.expires = options['expires']
        self.renamegzip = options['renamegzip']
        self.s3host = options['s3host']
        self.request_cloudfront_invalidation = options['invalidate']

        filter_list_from_settings = getattr(
            settings, 'AWS_S3_UPLOAD_FILTER_LIST', [])

        filter_list_from_cmd = options['filter_list']
        filter_list_from_cmd = filter_list_from_cmd.split(',')

        self.filter_list.extend(
            filter_list_from_cmd + filter_list_from_settings
        )

        self._walk_folders(dry_run=options['dry_run'])

        if self.request_cloudfront_invalidation:
            self._call_cloudfront_invalidation()

    def _create_s3_connection(self):
        """Creates a new connection to S3"""
        session_config = {
            'aws_access_key_id': self.AWS_S3_ACCESS_KEY_ID,
            'aws_secret_access_key': self.AWS_S3_SECRET_ACCESS_KEY,
        }

        if self.AWS_S3_REGION_NAME:
            session_config['region_name'] = self.AWS_S3_REGION_NAME

        session = boto3.Session(**session_config)

        client_config = {}

        if self.s3host:
            if not self.s3host.startswith(('http://', 'https://')):
                self.s3host = f'https://{self.s3host}'

            client_config['endpoint_url'] = self.s3host
            # Configure for S3-compatible services
            # that use path-style addressing
            client_config['config'] = boto3.session.Config(
                s3={
                    'addressing_style': 'path'
                }
            )

        client = session.client('s3', **client_config)
        resource = session.resource('s3', **client_config)

        # This is a trap because if always returns an object
        # even if the bucket does not exist. We need to explicitly
        # test if the bucket exists by calling head_bucket -- see below
        bucket = resource.Bucket(self.AWS_STORAGE_BUCKET_NAME)

        try:
            client.head_bucket(Bucket=self.AWS_STORAGE_BUCKET_NAME)

            if self.verbosity > 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Connected to existing bucket: {self.AWS_STORAGE_BUCKET_NAME}")
                )
        except ClientError as e:
            # If the bucket does not exist we receive
            # a 404 code and that will be the trigger
            # that will be using to create a new bucket
            error_code = e.response['Error']['Code']

            if error_code == '404':
                if self.verbosity > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Bucket {self.AWS_STORAGE_BUCKET_NAME} "
                            "not found. Attempting to create..."
                        )
                    )

                try:
                    create_bucket_config = {}

                    # For regions other than us-east-1, we need to specify LocationConstraint
                    if self.AWS_S3_REGION_NAME and self.AWS_S3_REGION_NAME != 'us-east-1':
                        create_bucket_config['CreateBucketConfiguration'] = {
                            'LocationConstraint': self.AWS_S3_REGION_NAME
                        }

                    client.create_bucket(
                        Bucket=self.AWS_STORAGE_BUCKET_NAME,
                        **create_bucket_config
                    )

                    waiter = client.get_waiter('bucket_exists')
                    waiter.wait(
                        Bucket=self.AWS_STORAGE_BUCKET_NAME,
                        WaiterConfig={'Delay': 2, 'MaxAttempts': 30}
                    )

                    if self.verbosity > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Created bucket: {self.AWS_STORAGE_BUCKET_NAME}"
                            )
                        )
                except ClientError as creation_error:
                    raise CommandError(
                        f"Failed to create bucket '{self.AWS_STORAGE_BUCKET_NAME}': "
                        f"{creation_error.response['Error']['Message']}"
                    )
            elif error_code == '403':
                raise CommandError(
                    f"Access denied to bucket '{self.AWS_STORAGE_BUCKET_NAME}'. "
                    f"Check your AWS credentials and bucket permissions."
                )
            else:
                raise CommandError(
                    f"Failed to access bucket '{self.AWS_STORAGE_BUCKET_NAME}': "
                    f"{e.response['Error']['Message']}"
                )

        self.stdout.write(
            self.style.NOTICE(
                f"Uploads will go to bucket: {bucket.name}"
            )
        )

        return client, bucket

    def _create_cloudfront_connection(self):
        return boto3.client('cloudfront')

    def _handle_upload(self, root, dirs, files, **params):
        """Function that uploads the directory and files to S3"""
        client = params.get('client')
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/bucket/index.html
        bucket = params.get('bucket')

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

        is_dry_run = params.get('dry_run', False)

        # NOTE: filename is the string filepath
        for filename in files:
            if filename in self.filter_list:
                continue

            # The full path to the file to upload
            # the actual key will be determined below
            fullpath = root.joinpath(filename)
            if fullpath.is_dir():
                continue

            # Get the parts of the path to the file
            # and create a relative path to the file
            # e.g. media/2010/01/01/file.txt
            list_parts = list(root.parts)
            parts = list_parts[list_parts.index(directory.name):]
            relative_path = '/'.join(parts)

            # This creates the final key or path that
            # will be used to save the file in s3
            file_key = f'{relative_path}/{filename}'

            if is_dry_run:
                self.stdout.write(
                    self.style.NOTICE(
                        f"    + Would upload {filename} to {file_key}"
                    )
                )
                continue

            # The files can be prefixed under a specific
            # main directory for organization
            if self.prefix:
                file_key = f'{self.prefix}/{file_key}'

            # Checks if the file on S3 is older
            # than the local files and if so uploads
            # it to the bucket
            if not self.force_upload:
                try:
                    result = client.head_object(
                        Bucket=self.AWS_STORAGE_BUCKET_NAME,
                        Key=file_key
                    )
                except ClientError as e:
                    # If the file does not exist in the bucket,
                    # head_object will return a 404 error
                    # we can safely ignore this and proceed
                    # to upload the file anyways
                    pass
                else:
                    if result:
                        # type: datetime.datetime
                        s3_last_modified = result['LastModified']

                        file_timestamp = os.stat(fullpath).st_mtime
                        file_datetime = datetime.datetime.fromtimestamp(
                            file_timestamp,
                            tz=datetime.timezone.utc
                        )

                        if file_datetime < s3_last_modified:
                            self.skip_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"    + File {file_key} has not been modified "
                                    "since last being uploaded"
                                )
                            )
                            continue

            content_type = mimetypes.guess_type(filename)[0]
            if content_type:
                extra_args.update(**{'ContentType': content_type})

            with open(fullpath, mode='rb') as f:
                file_size = os.fstat(f.fileno()).st_size
                file_data = f.read()

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
                        self.stdout.write(
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
                        self.stdout.write(f"Expires: {extra_args['Expires']}")
                        self.stdout.write(
                            f"Cache control: {extra_args['CacheControl']}")

                try:
                    if file_size > 100 * 1024 * 1024: # 100MB threshold
                        config = transfer.TransferConfig(
                            multipart_threshold=1024 * 25,  # 25MB
                            max_concurrency=10,
                            multipart_chunksize=1024 * 25,
                            use_threads=True
                        )

                        client.upload_file(
                            Filename=str(fullpath),
                            Bucket=self.AWS_STORAGE_BUCKET_NAME,
                            Key=file_key,
                            ExtraArgs=extra_args,
                            Config=config
                        )
                    else:
                        client.upload_file(
                            Filename=str(fullpath),
                            Bucket=self.AWS_STORAGE_BUCKET_NAME,
                            Key=file_key,
                            ExtraArgs=extra_args
                        )
                except ClientError as e:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to upload file: {filename}"))
                except (ClientError, NoCredentialsError, BotoCoreError) as e:
                    self.stdout.write(self.style.ERROR(str(e)))
                    raise
                else:
                    self.upload_count += 1
                    self.uploaded_files.append(fullpath)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    + OK Uploaded {filename} to {file_key}"
                        )
                    )

                # try:
                #     instance = transfer.S3Transfer(client=client)
                #     instance.upload_file(**{
                #         'filename': str(fullpath),
                #         'bucket': self.AWS_STORAGE_BUCKET_NAME,
                #         'key': file_key,
                #         'extra_args': extra_args
                #     })
                # except boto3.exceptions.S3TransferFailedError as e:
                #     print(f'Failed to upload file: {filename}')
                # except Exception as e:
                #     print(e)
                #     raise
                # else:
                #     self.upload_count += 1
                #     self.uploaded_files.append(fullpath)

    def _walk_folders(self, dry_run=False):
        """Method used to walk the static and media folders
        in order to discover the files that should be uploaded to S3"""
        self.stdout.write(
            self.style.NOTICE(
                f"Using S3 bucket: {self.AWS_STORAGE_BUCKET_NAME}"
            )
        )

        client, bucket = self._create_s3_connection()

        params = {
            'client': client,
            'bucket': bucket,
            'directory': None,
            'dry_run': dry_run
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
        if not self.AWS_CLOUDFRONT_DISTRIBUTION:
            raise CommandError(
                "An object invalidation was requested but AWS_CLOUDFRONT_DISTRIBUTION "
                "is not present in your settings"
            )

        connection = self._create_cloudfront_connection()

        # We can't send more than 1000 objects in the
        # same invalidation request
        def chunked(items, size=1000):
            for i in range(0, len(items), size):
                yield items[i:i + size]

        chunks = chunked(self.uploaded_files)

        for chunk in chunks:
            paths = list(chunk)
            connection.create_invalidation(
                DistributionId=self.AWS_CLOUDFRONT_DISTRIBUTION,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f"sync-s3-{int(time.time())}"
                }
                # Paths={
                #     'Quantity': len(paths), 
                #     'Items': list(paths)
                # }
            )

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
            help=(
                "Override the default S3 endpoint. Useful for S3-compatible services like "
                "MinIO, DigitalOcean Spaces, etc. Example: --s3host=https://nyc3.digitaloceanspaces.com "
                "or --s3host=minio.example.com:9000"
            )
        )
        parser.add_argument(
            "--invalidate",
            dest="invalidate",
            default=False,
            action="store_true",
            help="Invalidates the associated objects in CloudFront",
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help="Shows what would be uploaded without actually uploading"
        )
