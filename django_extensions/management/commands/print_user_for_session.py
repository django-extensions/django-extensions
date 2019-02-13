# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import importlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import VALID_KEY_CHARS
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = ("print the user information for the provided session key. "
            "this is very helpful when trying to track down the person who "
            "experienced a site crash.")

    def add_arguments(self, parser):
        parser.add_argument('session_id', nargs='+', type=str,
                            help='user session id')

    @signalcommand
    def handle(self, *args, **options):

        key = options['session_id'][0]

        if not set(key).issubset(set(VALID_KEY_CHARS)):
            raise CommandError("malformed session key")

        engine = importlib.import_module(settings.SESSION_ENGINE)

        if not engine.SessionStore().exists(key):
            print("Session Key does not exist. Expired?")
            return

        session = engine.SessionStore(key)
        data = session.load()

        print('Session to Expire: %s' % session.get_expiry_date())
        print('Raw Data: %s' % data)

        uid = data.get('_auth_user_id', None)

        if uid is None:
            print('No user associated with session')
            return

        print(u"User id: %s" % uid)

        User = get_user_model()
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            print("No user associated with that id.")
            return

        # use django standrd api for reporting
        print("full name: %s" % user.get_full_name())
        print("short name: %s" % user.get_short_name())
        print("username: %s" % user.get_username())
        if hasattr(user, 'email'):
            print("email: %s" % user.email)
