from django.core.management import call_command
from django.test import TestCase


class FindTemplateCase(TestCase):

    def setUp(self):
        self.existed_template = 'welcome.html'
        self.not_existed_template = 'welcome1.html'

    def test_find_template_for_existed(self):
        args = [self.existed_template]
        opts = {}
        call_command('find_template', *args, **opts)

    def test_find_template_for_not_existed(self):
        args = [self.not_existed_template]
        opts = {}
        with self.assertRaises(SystemExit):
            call_command('find_template', *args, **opts)
