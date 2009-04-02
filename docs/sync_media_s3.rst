sync_media_s3
=============

:synopsis: sync your MEDIA_ROOT folder to S3

Django command that scans all files in your settings.MEDIA_ROOT folder and
uploads them to S3 with the same directory structure.

This command can optionally do the following but it is off by default:

  * gzip compress any CSS and Javascript files it finds and adds the
    appropriate 'Content-Encoding' header.
  * set a far future 'Expires' header for optimal caching.


Example Usage
-------------

::

  # Upload files to S3 into the bucket 'mybucket'
  $ ./manage.py sync_media_s3 mybucket

::

  # Upload files to S3 into the bucket 'mybucket' and enable gzipping CSS/JS files and setting of a far future expires header
  $ ./manage.py sync_media_s3 mybucket --gzip --expires


Required libraries and settings
-------------------------------

This management command requires the boto library and was tested with version
1.4c:

  http://code.google.com/p/boto/

It also requires an account with Amazon Web Services (AWS) and the AWS S3 keys.
The keys are added to your settings.py file, for example::

  # settings.py
  AWS_ACCESS_KEY_ID = ''
  AWS_SECRET_ACCESS_KEY = ''
