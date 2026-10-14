import json
import os
from types import SimpleNamespace

import pytest
from django.core.management import call_command, CommandError
from django_extensions.management.commands.shell_plus import Command
from jupyter_client.kernelspec import KernelSpecManager


@pytest.fixture
def kernel_dirs(tmp_path, monkeypatch):
    kernels = tmp_path / "kernels"
    base = kernels / "python3"
    base.mkdir(parents=True)
    spec = {
        "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Python 3",
        "language": "python",
    }
    (base / "kernel.json").write_text(json.dumps(spec))
    manager = KernelSpecManager(kernel_dirs=[str(kernels)], user_kernel_dir=str(kernels))
    monkeypatch.setattr("jupyter_client.kernelspec.KernelSpecManager", lambda: manager)
    return kernels, spec


def test_install_kernel_without_notebook(kernel_dirs, settings, capsys):
    kernels, base_spec = kernel_dirs
    settings.IPYTHON_ARGUMENTS = ["--debug"]
    settings.IPYTHON_KERNEL_DISPLAY_NAME = "Project shell"
    call_command("shell_plus", "--install-kernel")
    installed = json.loads((kernels / "django_extensions" / "kernel.json").read_text())
    assert installed["display_name"] == "Project shell"
    assert installed["argv"] == base_spec["argv"] + ["--debug", "--ext", "django_extensions.management.notebook_extension"]
    assert settings.IPYTHON_ARGUMENTS == ["--debug"]
    assert json.loads((kernels / "python3" / "kernel.json").read_text()) == base_spec
    assert "django_extensions" in capsys.readouterr().out
    # Repeated deployment runs replace the generated spec without duplicating args.
    call_command("shell_plus", "--install-kernel")
    assert json.loads((kernels / "django_extensions" / "kernel.json").read_text()) == installed


def test_custom_kernel_name(kernel_dirs, settings):
    kernels, _ = kernel_dirs
    settings.IPYTHON_KERNEL_NAME = "project-shell"
    call_command("shell_plus", "--install-kernel")
    assert (kernels / "project-shell" / "kernel.json").exists()
    assert not (kernels / "django_extensions").exists()


@pytest.mark.parametrize("name", ["../outside", "", ".", "..", "with space", None])
def test_invalid_kernel_name(kernel_dirs, settings, name):
    settings.IPYTHON_KERNEL_NAME = name
    with pytest.raises(CommandError, match="IPYTHON_KERNEL_NAME"):
        call_command("shell_plus", "--install-kernel")


def test_missing_base_kernel(kernel_dirs, settings):
    settings.NOTEBOOK_KERNEL_SPEC_NAMES = ["does-not-exist"]
    with pytest.raises(CommandError, match="No notebook.*kernel specs found"):
        call_command("shell_plus", "--install-kernel")


def test_command_line_kernel_arguments(kernel_dirs, settings, monkeypatch, tmp_path):
    kernels, base_spec = kernel_dirs
    manage = tmp_path / "manage.py"
    manage.touch()
    monkeypatch.setattr("sys.argv", [str(manage)])
    settings.IPYTHON_ARGUMENTS = ["--unused"]
    Command().run_from_argv([str(manage), "shell_plus", "--install-kernel", "--", "--debug"])
    installed = json.loads((kernels / "django_extensions" / "kernel.json").read_text())
    assert installed["argv"] == base_spec["argv"] + ["--debug", "--ext", "django_extensions.management.notebook_extension"]
    assert str(tmp_path) in installed["env"]["PYTHONPATH"].split(os.pathsep)


@pytest.mark.parametrize("runner", ["--plain", "--lab", "--notebook", "--kernel"])
def test_install_is_exclusive(kernel_dirs, runner):
    with pytest.raises(CommandError, match="not allowed with argument"):
        call_command("shell_plus", "--install-kernel", runner)


def test_fallback_to_user_kernel_directory(kernel_dirs, monkeypatch, tmp_path):
    kernels, _ = kernel_dirs
    user_kernels = tmp_path / "user-kernels"
    manager = KernelSpecManager(kernel_dirs=[str(kernels)], user_kernel_dir=str(user_kernels))
    monkeypatch.setattr("jupyter_client.kernelspec.KernelSpecManager", lambda: manager)
    # A file in place of a directory makes the first destination unwritable.
    (kernels / "django_extensions").touch()
    call_command("shell_plus", "--install-kernel")
    assert (user_kernels / "django_extensions" / "kernel.json").exists()
    (user_kernels / "django_extensions" / "kernel.json").unlink()
    (user_kernels / "django_extensions").rmdir()
    (user_kernels / "django_extensions").touch()
    with pytest.raises(CommandError, match="Could not write kernel"):
        call_command("shell_plus", "--install-kernel")


def test_notebook_installs_overridden_specs_before_start(kernel_dirs):
    kernels, _ = kernel_dirs
    events = []

    class CustomCommand(Command):
        def generate_kernel_specs(self, app, arguments):
            events.append("generate")
            spec = self.load_base_kernel_spec(app)
            spec.argv.extend(arguments)
            return {"first": spec, "second": spec}

    def start():
        assert (kernels / "first" / "kernel.json").exists()
        assert (kernels / "second" / "kernel.json").exists()
        events.append("start")

    app = SimpleNamespace(
        kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]),
        start=start,
    )
    command = CustomCommand()
    command.run_notebookapp(lambda arguments: app, {"no_browser": True})
    assert events == ["generate", "start"]
    events.clear()
    call_command(command, "--install-kernel")
    assert events == ["generate"]


@pytest.mark.parametrize("name", ["python3", "Python3"])
def test_base_kernel_cannot_be_overwritten(kernel_dirs, settings, name):
    kernels, base_spec = kernel_dirs
    settings.IPYTHON_KERNEL_NAME = name
    with pytest.raises(CommandError, match="must differ from the base kernel"):
        call_command("shell_plus", "--install-kernel")
    assert json.loads((kernels / "python3" / "kernel.json").read_text()) == base_spec


def test_missing_jupyter_client(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def import_without_jupyter(name, *args, **kwargs):
        if name == "jupyter_client.kernelspec":
            raise ImportError("not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_jupyter)
    with pytest.raises(CommandError, match="requires jupyter-client"):
        call_command("shell_plus", "--install-kernel")
