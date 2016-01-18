# coding=utf-8
import django
import pytest
from django.core.management import call_command


class TestRunScript:

    def test_runs(self, capsys):
        # lame test...does it run?
        call_command('runscript', 'sample_script', verbosity=2)
        out = capsys.readouterr()[0]
        assert "Found script 'tests.testapp.scripts.sample_script'" in out
        assert "Running script 'tests.testapp.scripts.sample_script'" in out

    @pytest.mark.skipif(
        django.VERSION < (1, 7),
        reason="AppConfig and modify_settings appeared in 1.7"
    )
    def test_runs_appconfig(self, capsys):
        from django.test import modify_settings

        with modify_settings(INSTALLED_APPS={
            'append': 'tests.testapp.apps.TestAppConfig',
            'remove': 'tests.testapp',
        }):
            call_command('runscript', 'sample_script', verbosity=2)
            out = capsys.readouterr()[0]
            assert "Found script 'tests.testapp.scripts.sample_script'" in out
            assert "Running script 'tests.testapp.scripts.sample_script'" in out
