mail_debug
==========

:synopsis: Starts a mail server which echos out the contents of the email
  instead of sending it.

Installation
------------

This command requires installation of `aiosmtpd`_. You can get it from PyPI with::

    pip install aiosmtpd

.. _`aiosmtpd`: https://github.com/aio-libs/aiosmtpd

Usage
-----

You can start the mail server with the command::

    $ python manage.py mail_debug
    Now accepting mail at 127.0.0.1:1025 -- use CONTROL-C to quit

By default, it will start a process listening on port 1025 on local host.
Assuming your Django settings ``EMAIL_HOST`` and ``EMAIL_PORT`` are configured to
point to the same IP and port, in another terminal, open the Django shell and run

.. code-block:: python

    from django.core.mail import send_mail

    send_mail(
        "Subject here",
        "Here is the message.",
        "from@example.com",
        ["to@example.com"],
        fail_silently=False,
    )

If you go back to the terminal with the ``mail_debug`` command is running, you
should see the email coming through::

    ---------- MESSAGE FOLLOWS ----------
    Content-Type: text/plain; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: Subject here
    From: from@example.com
    To: to@example.com
    Date: Sun, 19 Jan 2025 12:21:47 -0000
    Message-ID:
     <173728930732.90349.12519699486821706188@1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa>
    X-Peer: 127.0.0.1

    Here is the message.
    ------------ END MESSAGE ------------



Arguments
---------

You can specify a different port by passing it as argument to the command::

    $ python manage.py mail_debug 1026
    Now accepting mail at 127.0.0.1:1026 -- use CONTROL-C to quit

You can also pass the host + port separated by a colon, e.g.::

    $ python manage.py mail_debug 192.168.1.1:1234
    Now accepting mail at 192.168.1.1:1234 -- use CONTROL-C to quit

Options
-------

The command also accepts the following options:

* ``--output``: Specifies an output file to send a copy of all messages (not flushed immediately).

* ``--use-settings``: Uses EMAIL_HOST and HOST_PORT from Django settings. This option is ignored if the address
  or port is passed as an argument
