"""
Pluggable development environment.

Example to add a thread to this command, somewhere that will be imported at
startup (ie. yourproject/models.py if you added yourproject to
INSTALLED_APPS)::

    import os

    from crudlfap.management.commands.dev import Command, CommandThread

    Command.threads.append(
        CommandThread(
            name='npm-watch',
            cmd='npm start -- --watch',
            cwd=os.path.abspath(
                # should be path to package.json
                os.path.join(os.path.dirname(__file__), '..', '..')
            )
        )
    )
"""

import os
import os.path
import secrets
import string
import subprocess
import shutil
import sys
import threading
import time

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.timezone import now

try:
    import devpy.develop as logger
except ImportError:
    import logging
    logger = logging.getLogger('dev')


def rnpw(num=28):
    return ''.join(secrets.choice(
        string.ascii_uppercase + string.digits) for _ in range(num))


class SigFinish(Exception):
    """Blocking thread interruption "hack".

    http://pydev.blogspot.fr/2013/01/interrupting-python-thread-with-signals.html
    """
    pass


def throw_signal_function(frame, event, arg):
    """Callback to raise :py:class:`SigFinish`."""
    raise SigFinish()


def interrupt_thread(thread):
    """Interrupt a thread using :py:func:`throw_signal_function`."""

    for thread_id, frame in sys._current_frames().items():
        if thread_id == thread.ident:  # Note: Python 2.6 onwards
            set_trace_for_frame_and_parents(frame, throw_signal_function)

            while thread in [t for t in threading.enumerate()]:
                time.sleep(3)


def set_trace_for_frame_and_parents(frame, trace_func):
    """
    Set the trace for frame and parents.

    Note: this only really works if there's a tracing function set in this
    thread (i.e.: sys.settrace or threading.settrace must have set the function
    before).
    """
    while frame:
        if frame.f_trace is None:
            frame.f_trace = trace_func
        frame = frame.f_back
    del frame


class BaseThread(threading.Thread):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.running = False

    def run(self):
        sys.settrace(lambda *a, **k: None)

        try:
            while True:
                logger.info('{}: Start'.format(self))
                try:
                    self.running = True
                    self.callback()
                except Exception as e:
                    self.running = False
                    raise
                else:
                    self.running = False
                    logger.info('{}: Clean exit'.format(self))

        except SigFinish:
            logger.info('{}: SigFinish'.format(self))

    def __str__(self):
        return self.name


class CommandThread(BaseThread):
    def __init__(self, name, cmd, cwd=None):
        super().__init__(name)
        self.cmd = cmd
        self.cwd = cwd

    def callback(self):
        watch = '.dev.{}.pid'.format(self)

        if os.path.exists(watch):
            with open(watch, 'r') as f:
                pid = f.read().strip()

            if pid:
                pid = int(pid)
                if os.path.exists('/proc/{}'.format(pid)):
                    os.kill(pid, 9)

            os.unlink(watch)

        process = subprocess.Popen(
            [self.cmd],
            shell=True,
            cwd=self.cwd,
        )
        with open(watch, 'w+') as f:
            f.write(str(process.pid))
        process.communicate()


class Command(BaseCommand):
    help = 'Start development environment'
    threads = [
        CommandThread('runserver', '{} runserver'.format(sys.argv[0]))
    ]
    if shutil.which('npm'):
        threads.append(
            CommandThread(
                name='npm-start',
                cmd='npm start',
                cwd=os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..', '..')
                )
            )
        )

    def handle(self, *args, **options):
        call_command('migrate')
        self.createusers()

        try:
            for thread in self.threads:
                thread.start()
        except KeyboardInterrupt:
            for t in threading.enumerate():
                interrupt_thread(t)
            raise

    def createusers(self):
        user_model = apps.get_model(settings.AUTH_USER_MODEL)

        def createuser(username, **defaults):
            user, created = user_model.objects.update_or_create(
                username=username,
                defaults=defaults,
            )

            last_login = None
            if user.last_login:
                last_login = now() - user.last_login

            if created or (last_login and last_login.seconds >= 3600):
                password = rnpw()
                user.set_password(password)
                user.save()
                logger.warning('\n{}\nLogin with {} / {}\n'.format(
                    '*' * 12, username, password))

            return user, created

        createuser('dev', is_staff=True, is_superuser=True)
        createuser('staff', is_staff=True)
        createuser('user')
