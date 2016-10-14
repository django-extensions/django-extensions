sync_s3
=======

:synopsis: sync your MEDIA_ROOT and STATIC_ROOT folders to S3

Django command that scans all files in your settings.MEDIA_ROOT and
settings.STATIC_ROOT folders, then uploads them to S3 with the same
directory structure.

This command can optionally do the following but it is off by default:

  * gzip compress any CSS and Javascript files it finds and adds the
    appropriate 'Content-Encoding' header.
  * set a far future 'Expires' header for optimal caching.
  * upload only media or static files.
  * use any other provider compatible with Amazon S3.
  * set other than 'public-read' ACL.

Example Usage
-------------

::

  # Upload files to S3 into the bucket 'mybucket'
  $ ./manage.py sync_s3 mybucket

::

  # Upload files to S3 into the bucket 'mybucket' and enable gzipping CSS/JS files and setting of a far future expires header
  $ ./manage.py sync_s3 mybucket --gzip --expires

::

  # Upload only media files to S3 into the bucket 'mybucket'
  $ ./manage.py sync_s3 mybucket  --media-only  # or --static-only

::

  # Upload only media files to a S3 compatible provider into the bucket 'mybucket' and set private file ACLs
  $ ./manage.py sync_s3 mybucket  --media-only  --s3host=cs.example.com --acl=private

Required libraries and settings
-------------------------------

This management command requires the boto library and was tested with version
1.4c:

  https://github.com/boto/boto

It also requires an account with Amazon Web Services (AWS) and the AWS S3 keys.
Bucket name is required and cannot be empty.
The keys and bucket name are added to your settings.py file, for example::

  # settings.py
  AWS_ACCESS_KEY_ID = ''
  AWS_SECRET_ACCESS_KEY = ''
  AWS_BUCKET_NAME = 'bucket'

Optional settings
-----------------

It is possible to customize sync_s3 directly from django settings file, for example::

  # settings.py
  AWS_S3_HOST = 'cs.example.com'
  AWS_DEFAULT_ACL = 'private'
  SYNC_S3_PREFIX = 'some_prefix'
  FILTER_LIST = 'dir1, dir2'
  AWS_CLOUDFRONT_DISTRIBUTION = 'E27LVI50CSW06W'
  SYNC_S3_RENAME_GZIP_EXT = '.gz'
