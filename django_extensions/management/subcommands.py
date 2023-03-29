# -*- coding: utf-8 -*-
import sys

from django.core.management import BaseCommand as _BaseCommand


class SubCommand(object):
    """
    The sub-command class for handle the sub-command of Django command.

    This class is similar to ``django.core.management.BaseCommand``, you can override the
    following methods for sub-command:

        - ``add_arguments``: for handle the arguments.
        - ``handle``: for handle the command perform.
          ** NOTICE **: YOU MUST IMPLEMENT THIS METHOD ELSE EXCEPTION WILL RAISED.

    """
    name = ""
    """ sub-command name """

    help = ""
    """ sub-command help for ``help``. """

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        raise NotImplementedError()


class BaseCommand(_BaseCommand):
    """
    This class is used to simplify the development of sub commands.

    Basic Usage
    --------------------------------------------------

        1. Define the sub-command:

            - Inherits from the ``SubCommand`` class and implements the ``handle`` method, or
            - Declare a class and provide the followings:
                - ``name`` attribute for the sub-command name,
                - ``add_arguments(parser)`` and ``handle(*args, **options)`` methods.

        2. Define the command class:

            - Replace the ``django.core.management.BaseCommand`` with
              ``django_extensions.management.subcommands.BaseCommand``,

            - Declare the attributes:
                - ``sub_command_classes``, a array (``list`` or ``tuple``) for define the sub-command classes.

        Example:

            >>> class FooSubCommand(SubCommand):
            ...     name = 'foo'
            ...     def handle(self, *args, **options):
            ...         self.stdout.write("Foo")
            ...
            ... class Command(BaseCommand):
            ...     sub_command_classes = [ FooSubCommand ]


    """

    sub_command_classes = []
    """ the sub-command classes. """

    def init_sub_command(self, sub_command):
        """
        Initial the sub command object.

        :param sub_command: Sub-command object.
        """
        sub_command.stderr = self.stderr
        sub_command.stdout = self.stdout
        sub_command.root_command = self

    @property
    def sub_commands(self):
        """
        Return the sub-commands array.
        """
        ret = []
        for sub_command_class in self.sub_command_classes:
            sub_command = sub_command_class()
            self.init_sub_command(sub_command)
            ret.append(sub_command)
        return ret

    def get_sub_command_kwargs(self, sub_command):
        kwargs = {
            'name': sub_command.name,
        }
        if sub_command.help:
            kwargs['help'] = sub_command.help
        return kwargs

    def add_arguments(self, parser):
        self.parser = parser
        sub_parsers = parser.add_subparsers()

        all_sub_commands = self.sub_commands
        if all_sub_commands:
            for sub_command in all_sub_commands:
                kwargs = self.get_sub_command_kwargs(sub_command)
                sub_parser = sub_parsers.add_parser(**kwargs)
                sub_parser.set_defaults(func=sub_command.handle)

                sub_command.add_arguments(sub_parser)
        self.sub_parsers = sub_parsers

    def default_handler(self, *args, **options):
        """
        Call this method if no any sub-command found.
        """
        self.parser.print_help()

    def handle(self, *args, **options):
        handler = options.get('func') or self.default_handler
        try:
            return handler(*args, **options)
        except Exception as exc:
            self.stderr.write("Execute command fail: %s" % str(exc))
            sys.exit(1)
