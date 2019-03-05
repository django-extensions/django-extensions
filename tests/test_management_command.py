# -*- coding: utf-8 -*-
import mock
import os
import sys
import logging
import importlib

from django.core.management import call_command, find_commands, load_command_class
from django.db import models
from django.test import TestCase
from six import StringIO, PY3

from django_extensions.management.modelviz import use_model, generate_graph_data
from django_extensions.management.commands.merge_model_instances import \
    get_model_to_deduplicate, \
    get_field_names, \
    keep_first_or_last_instance
from . import force_color_support
from .testapp.models import Person, Name, Note, Personality, Club, Membership, \
    Permission
from .testapp.jobs.hourly.test_hourly_job import HOURLY_JOB_MOCK
from .testapp.jobs.daily.test_daily_job import DAILY_JOB_MOCK
from .testapp.jobs.weekly.test_weekly_job import WEEKLY_JOB_MOCK
from .testapp.jobs.monthly.test_monthly_job import MONTHLY_JOB_MOCK
from .testapp.jobs.yearly.test_yearly_job import YEARLY_JOB_MOCK


class MockLoggingHandler(logging.Handler):
    """ Mock logging handler to check for expected logs. """

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }


class CommandTest(TestCase):
    def test_error_logging(self):
        # Ensure command errors are properly logged and reraised
        from django_extensions.management.base import logger
        logger.addHandler(MockLoggingHandler())
        module_path = "tests.management.commands.error_raising_command"
        module = importlib.import_module(module_path)
        error_raising_command = module.Command()
        self.assertRaises(Exception, error_raising_command.execute)
        handler = logger.handlers[0]
        self.assertEqual(len(handler.messages['error']), 1)


class ShowTemplateTagsTests(TestCase):
    def test_some_output(self):
        out = StringIO()
        call_command('show_template_tags', stdout=out)
        output = out.getvalue()
        # Once django_extension is installed during tests it should appear with
        # its templatetags
        self.assertIn('django_extensions', output)
        # let's check at least one
        self.assertIn('syntax_color', output)


class AdminGeneratorTests(TestCase):
    def test_command(self):
        out = StringIO()
        call_command('admin_generator', 'django_extensions', stdout=out)
        output = out.getvalue()
        self.assertIn("@admin.register(Secret)", output)
        self.assertIn("class SecretAdmin(admin.ModelAdmin):", output)
        if PY3:
            self.assertIn("list_display = ('id', 'name', 'text')", output)
            self.assertIn("search_fields = ('name',)", output)
        else:
            self.assertIn("list_display = (u'id', u'name', u'text')", output)
            self.assertIn("search_fields = (u'name',)", output)


class DescribeFormTests(TestCase):
    def test_command(self):
        out = StringIO()
        call_command('describe_form', 'django_extensions.Secret', stdout=out)
        output = out.getvalue()
        self.assertIn("class SecretForm(forms.Form):", output)
        self.assertRegexpMatches(output, r"name = forms.CharField\(.*max_length=255")
        self.assertRegexpMatches(output, r"name = forms.CharField\(.*required=False")
        self.assertRegexpMatches(output, r"name = forms.CharField\(.*label=u?'Name'")
        self.assertRegexpMatches(output, r"text = forms.CharField\(.*required=False")
        self.assertRegexpMatches(output, r"text = forms.CharField\(.*label=u?'Text'")


class UpdatePermissionsTests(TestCase):
    def test_works(self):

        class PermModel(models.Model):
            class Meta:
                app_label = 'django_extensions'
                permissions = (('test_permission', 'test_permission'),)

        original_stdout = sys.stdout
        out = sys.stdout = StringIO()
        call_command('update_permissions', stdout=out, verbosity=3)
        sys.stdout = original_stdout
        self.assertIn("Can change perm model", out.getvalue())


class CommandSignalTests(TestCase):
    pre = None
    post = None

    def test_works(self):
        from django_extensions.management.signals import post_command, \
            pre_command
        from django_extensions.management.commands.show_template_tags import \
            Command

        def pre(sender, **kwargs):
            CommandSignalTests.pre = dict(**kwargs)

        def post(sender, **kwargs):
            CommandSignalTests.post = dict(**kwargs)

        pre_command.connect(pre, Command)
        post_command.connect(post, Command)

        out = StringIO()
        call_command('show_template_tags', stdout=out)

        self.assertIn('args', CommandSignalTests.pre)
        self.assertIn('kwargs', CommandSignalTests.pre)

        self.assertIn('args', CommandSignalTests.post)
        self.assertIn('kwargs', CommandSignalTests.post)
        self.assertIn('outcome', CommandSignalTests.post)


class CommandClassTests(TestCase):
    def setUp(self):
        management_dir = os.path.join('django_extensions', 'management')
        self.commands = find_commands(management_dir)

    def test_load_commands(self):
        """Try to load every management command to catch exceptions."""
        try:
            for command in self.commands:
                load_command_class('django_extensions', command)
        except Exception as e:
            self.fail("Can't load command class of {0}\n{1}".format(command, e))


class GraphModelsTests(TestCase):
    """
    Tests for the `graph_models` management command.
    """
    def test_use_model(self):
        include_models = [
            'NoWildcardInclude',
            'Wildcard*InsideInclude',
            '*WildcardPrefixInclude',
            'WildcardSuffixInclude*',
            '*WildcardBothInclude*'
        ]
        exclude_models = [
            'NoWildcardExclude',
            'Wildcard*InsideExclude',
            '*WildcardPrefixExclude',
            'WildcardSuffixExclude*',
            '*WildcardBothExclude*'
        ]
        # Any model name should be used if neither include or exclude
        # are defined.
        self.assertTrue(use_model(
            'SomeModel',
            None,
            None
        ))
        # Any model name should be allowed if `*` is in `include_models`.
        self.assertTrue(use_model(
            'SomeModel',
            ['OtherModel', '*', 'Wildcard*Model'],
            None
        ))
        # No model name should be allowed if `*` is in `exclude_models`.
        self.assertFalse(use_model(
            'SomeModel',
            None,
            ['OtherModel', '*', 'Wildcard*Model']
        ))
        # Some tests with the `include_models` defined above.
        self.assertFalse(use_model(
            'SomeModel',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'NoWildcardInclude',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'WildcardSomewhereInsideInclude',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'MyWildcardPrefixInclude',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'WildcardSuffixIncludeModel',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'MyWildcardBothIncludeModel',
            include_models,
            None
        ))
        # Some tests with the `exclude_models` defined above.
        self.assertTrue(use_model(
            'SomeModel',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'NoWildcardExclude',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'WildcardSomewhereInsideExclude',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'MyWildcardPrefixExclude',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'WildcardSuffixExcludeModel',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'MyWildcardBothExcludeModel',
            None,
            exclude_models
        ))

    def test_no_models_dot_py(self):
        data = generate_graph_data(['testapp_with_no_models_file'])
        self.assertEqual(len(data['graphs']), 1)

        model_name = data['graphs'][0]['models'][0]['name']
        self.assertEqual(model_name, 'TeslaCar')


class ShowUrlsTests(TestCase):
    """
    Tests for the `show_urls` management command.
    """
    def test_color(self):
        with force_color_support:
            out = StringIO()
            call_command('show_urls', stdout=out)
            self.output = out.getvalue()
            self.assertIn('\x1b', self.output)

    def test_no_color(self):
        with force_color_support:
            out = StringIO()
            call_command('show_urls', '--no-color', stdout=out)
            self.output = out.getvalue()
            self.assertNotIn('\x1b', self.output)


class MergeModelInstancesTests(TestCase):
    """
    Tests for the `merge_model_instances` management command.
    """

    @mock.patch('django_extensions.management.commands.merge_model_instances.apps.get_models')
    @mock.patch('django_extensions.management.commands.merge_model_instances.input')
    def test_get_model_to_merge(self, test_input, get_models):
        class Model(object):
            __name__ = ""

        return_value = []
        for v in ["one", "two", "three"]:
            instance = Model()
            instance.__name__ = v
            return_value.append(instance)
        get_models.return_value = return_value
        test_input.return_value = 2
        model_to_deduplicate = get_model_to_deduplicate()
        self.assertEqual(model_to_deduplicate.__name__, "two")

    @mock.patch('django_extensions.management.commands.merge_model_instances.input')
    def test_get_field_names(self, test_input):

        class Field(object):
            name = ""

            def __init__(self, name):
                self.name = name

        class Model(object):
            __name__ = ""
            one = Field(name="one")
            two = Field(name="two")
            three = Field(name="three")

        return_value = [Model().__getattribute__(field) for field in dir(Model()) if not field.startswith("__")]
        Model._meta = mock.MagicMock()
        Model._meta.get_fields = mock.MagicMock(return_value=return_value)

        # Choose the second return_value
        test_input.side_effect = [2, "C"]
        field_names = get_field_names(Model())
        # Test that the second return_value returned
        self.assertEqual(field_names, [return_value[1].name])

    @mock.patch('django_extensions.management.commands.merge_model_instances.input')
    def test_keep_first_or_last_instance(self, test_input):
        test_input.side_effect = ["xxxx", "first", "last"]
        first_or_last = keep_first_or_last_instance()
        self.assertEqual(first_or_last, "first")
        first_or_last = keep_first_or_last_instance()
        self.assertEqual(first_or_last, "last")

    @mock.patch('django_extensions.management.commands.merge_model_instances.get_model_to_deduplicate')
    @mock.patch('django_extensions.management.commands.merge_model_instances.get_field_names')
    @mock.patch('django_extensions.management.commands.merge_model_instances.keep_first_or_last_instance')
    def test_merge_model_instances(self, keep_first_or_last_instance, get_field_names, get_model_to_deduplicate):
        get_model_to_deduplicate.return_value = Person
        get_field_names.return_value = ["name"]
        keep_first_or_last_instance.return_value = "first"

        name = Name.objects.create(name="Name")
        note = Note.objects.create(note="This is a note.")
        personality_1 = Personality.objects.create(
            description="Child 1's personality.")
        personality_2 = Personality.objects.create(
            description="Child 2's personality.")
        child_1 = Person.objects.create(
            name=Name.objects.create(name="Child1"),
            age=10,
            personality=personality_1
        )
        child_1.notes.add(note)
        child_2 = Person.objects.create(
            name=Name.objects.create(name="Child2"),
            age=10,
            personality=personality_2
        )
        child_2.notes.add(note)

        club1 = Club.objects.create(name="Club one")
        club2 = Club.objects.create(name="Club two")
        person_1 = Person.objects.create(
            name=name,
            age=50,
            personality=Personality.objects.create(
                description="First personality")
        )
        person_1.children.add(child_1)
        person_1.notes.add(note)
        Permission.objects.create(text="Permission", person=person_1)

        person_2 = Person.objects.create(
            name=name,
            age=50,
            personality=Personality.objects.create(
                description="Second personality")
        )
        person_2.children.add(child_2)
        new_note = Note.objects.create(note="This is a new note")
        person_2.notes.add(new_note)
        Membership.objects.create(club=club1, person=person_2)
        Membership.objects.create(club=club1, person=person_2)
        Permission.objects.create(text="Permission", person=person_2)

        person_3 = Person.objects.create(
            name=name,
            age=50,
            personality=Personality.objects.create(
                description="Third personality")
        )
        person_3.children.add(child_2)
        person_3.notes.add(new_note)
        Membership.objects.create(club=club2, person=person_3)
        Membership.objects.create(club=club2, person=person_3)
        Permission.objects.create(text="Permission", person=person_3)

        self.assertEqual(Person.objects.count(), 5)
        self.assertEqual(Membership.objects.count(), 4)
        out = StringIO()
        call_command('merge_model_instances', stdout=out)
        self.ouptput = out.getvalue()
        self.assertEqual(Person.objects.count(), 3)
        person = Person.objects.get(name__name="Name")
        self.assertRaises(
            Person.DoesNotExist,
            lambda: Person.objects.get(
                personality__description="Second personality"))
        self.assertEqual(person.notes.count(), 2)
        self.assertEqual(person.clubs.distinct().count(), 2)
        self.assertEqual(person.permission_set.count(), 3)
        self.assertRaises(
            Personality.DoesNotExist,
            lambda: Personality.objects.get(description="Second personality"))


class RunJobsTests(TestCase):
    """
    Tests for the `runjobs` management command.
    """

    @mock.patch('django_extensions.management.commands.runjobs.Command.runjobs_by_signals')
    @mock.patch('django_extensions.management.commands.runjobs.Command.runjobs')
    @mock.patch('django_extensions.management.commands.runjobs.Command.usage_msg')
    def test_runjobs_management_command(
            self, usage_msg, runjobs, runjobs_by_signals):
        when = 'daily'
        call_command('runjobs', when)
        usage_msg.assert_not_called()
        runjobs.assert_called_once()
        runjobs_by_signals.assert_called_once()
        self.assertEqual(runjobs.call_args[0][0], when)

    @mock.patch('django_extensions.management.commands.runjobs.Command.runjobs_by_signals')
    @mock.patch('django_extensions.management.commands.runjobs.Command.runjobs')
    @mock.patch('django_extensions.management.commands.runjobs.Command.usage_msg')
    def test_runjobs_management_command_invalid_when(
            self, usage_msg, runjobs, runjobs_by_signals):
        when = 'invalid'
        call_command('runjobs', when)
        usage_msg.assert_called_once_with()
        runjobs.assert_not_called()
        runjobs_by_signals.assert_not_called()

    def test_runjobs_integration_test(self):
        jobs = [
            ("hourly", HOURLY_JOB_MOCK),
            ("daily", DAILY_JOB_MOCK),
            ("monthly", MONTHLY_JOB_MOCK),
            ("weekly", WEEKLY_JOB_MOCK),
            ("yearly", YEARLY_JOB_MOCK),
        ]

        # Reset all mocks in case they have been called elsewhere.
        for job in jobs:
            job[1].reset_mock()

        counter = 1
        for job in jobs:
            call_command('runjobs', job[0], verbosity=2)
            for already_called in jobs[:counter]:
                already_called[1].assert_called_once_with()
            for not_yet_called in jobs[counter:]:
                not_yet_called[1].assert_not_called()
            counter += 1

    def test_runjob_integration_test(self):
        jobs = [
            ("test_hourly_job", HOURLY_JOB_MOCK),
            ("test_daily_job", DAILY_JOB_MOCK),
            ("test_monthly_job", MONTHLY_JOB_MOCK),
            ("test_weekly_job", WEEKLY_JOB_MOCK),
            ("test_yearly_job", YEARLY_JOB_MOCK),
        ]

        # Reset all mocks in case they have been called elsewhere.
        for job in jobs:
            job[1].reset_mock()

        counter = 1
        for job in jobs:
            call_command('runjob', job[0], verbosity=2)
            for already_called in jobs[:counter]:
                already_called[1].assert_called_once_with()
            for not_yet_called in jobs[counter:]:
                not_yet_called[1].assert_not_called()
            counter += 1
