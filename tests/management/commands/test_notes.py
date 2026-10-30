import os

from django.core.management import call_command
from django_extensions.management.commands.notes import Command


def test_tag_filter_continues_after_other_tags(capsys, settings, tmp_path):
    settings.INSTALLED_APPS = []
    settings.TEMPLATES = [{**settings.TEMPLATES[0], "DIRS": [str(tmp_path)]}]
    template_path = tmp_path / "mixed.html"
    template_path.write_text(
        "{# TODO Ignore the first annotation. #}\n"
        "{# FIXME Keep the second annotation. #}\n"
        "{# NOTE Ignore another annotation. #}\n"
        "{# FIXME Keep the fourth annotation. #}\n"
    )

    call_command(Command(), "--tag=fixme")
    out, err = capsys.readouterr()

    assert "[  2] FIXME Keep the second annotation." in out
    assert "[  4] FIXME Keep the fourth annotation." in out
    assert "Ignore" not in out


def test_without_args(capsys, settings):
    call_command("notes")

    out, err = capsys.readouterr()
    print([out])
    assert (
        "tests/testapp/file_without_utf8_notes.py:\n  * [  1] TODO  this is a test todo\n\n"
        in out
    )


def test_with_utf8(capsys, settings):
    call_command("notes")

    out, err = capsys.readouterr()
    assert (
        "tests/testapp/file_with_utf8_notes.py:\n  * [  1] TODO  Russian text followed: Это техт на кириллице\n\n"
        in out
    )


def test_with_template_dirs(capsys, settings, tmpdir_factory):
    templates_dirs_path = tmpdir_factory.getbasetemp().strpath
    template_path = os.path.join(templates_dirs_path, "fixme.html")
    os.mkdir(os.path.join(templates_dirs_path, "sub.path"))
    sub_path = os.path.join(templates_dirs_path, "sub.path", "todo.html")
    settings.TEMPLATES[0]["DIRS"] = [templates_dirs_path]
    with open(template_path, "w") as f:
        f.write(
            """{# FIXME This is a comment. #}
{# TODO Do not show this. #}"""
        )
    with open(sub_path, "w") as f:
        f.write(
            """{# FIXME This is a second comment. #}
{# TODO Do not show this. #}"""
        )

    call_command("notes", "--tag=FIXME")
    out, err = capsys.readouterr()

    assert "{}:\n  * [  1] FIXME This is a comment.".format(template_path) in out
    assert "{}:\n  * [  1] FIXME This is a second comment.".format(sub_path) in out
    assert "TODO Do not show this." not in out


def test_with_template_sub_dirs(capsys, settings, tmpdir_factory):
    templates_dirs_path = tmpdir_factory.getbasetemp().strpath
    os.mkdir(os.path.join(templates_dirs_path, "test.path"))
    template_path = os.path.join(templates_dirs_path, "test.path", "fixme.html")
    settings.TEMPLATES[0]["DIRS"] = [templates_dirs_path]
    with open(template_path, "w") as f:
        f.write(
            """{# FIXME This is a comment. #}
{# TODO Do not show this. #}"""
        )

    call_command("notes", "--tag=FIXME")
    out, err = capsys.readouterr()

    assert "{}:\n  * [  1] FIXME This is a comment.".format(template_path) in out
    assert "TODO Do not show this." not in out
