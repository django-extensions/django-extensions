export_emails
=============

:synopsis: export the email addresses for your users in one of many formats

Most Django sites include a registered user base. There are times when you
would like to import these e-mail addresses into other systems (generic mail
program, Gmail, Google Docs invites, give edit permissions, LinkedIn Group
pre-approved listing, etc.). The export_emails command extension gives you this
ability. Exported users can be filtered by Group name association.


Example Usage
-------------

::

  # Export all the addresses in the '"First Last" <my@addr.com>;' format.
  $ ./manage.py export_emails > addresses.txt

::

  # Export users from the group 'Attendees' in the linked in pre-approve Group csv format.
  $ ./manage.py export_emails -g Attendees -f linkedin pycon08.csv

::

  # Create a csv file importable by Gmail or Google Docs
  $ ./manage.py export_emails --format=google google.csv


Supported Formats
-----------------

address
^^^^^^^

This is the default basic text format. Each entry is on its own line in the
format::

  "First Last" <user@host.com>;

This can be used with all known mail programs (that I know about anyway).


google
^^^^^^

A CSV (comma separated value) format which Google applications can import.
This can be used to import directly into Gmail, a Gmail mailing group, Google
Docs invite (to read), Google Docs grant edit permissions, Google Calendar
invites, etc.

Only two columns are supplied. One for the person's name and one for the email address.
This is also nice for importing into spreadsheets.


outlook
^^^^^^^

A CSV (comma separated value) format which Outlook can parse and import.
Supplies all the columns that Outlook 'requires', but only the name and email
address are supplied.


linkedin
^^^^^^^^

A CSV (comma separated value) format which can be imported by `LinkedIn Groups`_
to pre-approve a list of people for joining the group.

This supplies 3 columns: first name, last name, and email address. This is the
best generic csv file for importing into spreadsheets as well.


vcard
^^^^^

A vCard format which Apple Address Book can parse and import.

.. _`LinkedIn Groups`: http://www.linkedin.com/static?key=groups_info
