import sys
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class ShowPermissionsTests(TestCase):
    def _run_command(self, *args, **kwargs):
        """
        Utility to run the command and return captured output.
        """
        out = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = out
        try:
            call_command("show_template_paths", *args, **kwargs)
        finally:
            sys.stdout = sys_stdout
        return out.getvalue()

    def test_should_list_template_paths(self):
        output = [x for x in self._run_command().splitlines()]
        for template_path in [
            "tests/test_templates",
            "django/contrib/auth/templates",
            "django/contrib/admin/templates",
            "tests/testapp/templates",
            "django_extensions/templates",
        ]:
            self.assertTrue(
                any(path.endswith(template_path) for path in output),
                f"Could not find a template path ending with {template_path}",
            )
