from django.core.management import call_command
from unittest import mock


def test_initialize_mail_server():
    command = "django_extensions.management.commands.mail_debug"
    with (
        mock.patch(f"{command}.Controller") as controller,
        mock.patch(f"{command}.asyncio.new_event_loop") as new_event_loop,
        mock.patch(
            # Python 3.14+ raises this when the thread has no current event loop.
            f"{command}.asyncio.get_event_loop",
            side_effect=RuntimeError("There is no current event loop"),
        ),
    ):
        call_command("mail_debug", "2525")

    controller.assert_called_once()
    assert controller.call_args.kwargs == {"hostname": "127.0.0.1", "port": 2525}
    controller.return_value.start.assert_called_once_with()
    new_event_loop.return_value.run_forever.assert_called_once_with()
    new_event_loop.return_value.close.assert_called_once_with()
