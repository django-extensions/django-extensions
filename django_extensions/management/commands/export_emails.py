# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from django_extensions.compat import csv_writer as writer
from django_extensions.management.utils import signalcommand


FORMATS = [
    'address',
    'emails',
    'google',
    'outlook',
    'linkedin',
    'vcard',
]


def full_name(first_name, last_name, username, **extra):
    """Return full name or username."""
    name = " ".join(n for n in [first_name, last_name] if n)
    if not name:
        return username
    return name


class Command(BaseCommand):
    help = "Export user email address list in one of a number of formats."
    args = "[output file]"
    label = 'filename to save to'

    can_import_settings = True
    encoding = 'utf-8'  # RED_FLAG: add as an option -DougN

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.UserModel = get_user_model()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--group', '-g', action='store', dest='group', default=None,
            help='Limit to users which are part of the supplied group name',
        ),
        parser.add_argument(
            '--format', '-f', action='store', dest='format', default=FORMATS[0],
            help="output format. May be one of %s." % ", ".join(FORMATS),
        )

    @signalcommand
    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("extra arguments supplied")
        group = options['group']
        if group and not Group.objects.filter(name=group).count() == 1:
            names = "', '".join(g['name'] for g in Group.objects.values('name'))
            if names:
                names = "'" + names + "'."
            raise CommandError("Unknown group '" + group + "'. Valid group names are: " + names)

        UserModel = get_user_model()
        qs = UserModel.objects.all().order_by('last_name', 'first_name', 'username', 'email')
        if group:
            qs = qs.filter(groups__name=group).distinct()
        qs = qs.values('last_name', 'first_name', 'username', 'email')
        getattr(self, options['format'])(qs)

    def address(self, qs):
        """
        Single entry per line in the format of:
            "full name" <my@address.com>;
        """
        self.stdout.write("\n".join('"%s" <%s>;' % (full_name(**ent), ent['email']) for ent in qs))
        self.stdout.write("\n")

    def emails(self, qs):
        """
        Single entry with email only in the format of:
            my@address.com,
        """
        self.stdout.write(",\n".join(ent['email'] for ent in qs))
        self.stdout.write("\n")

    def google(self, qs):
        """CSV format suitable for importing into google GMail"""
        csvf = writer(sys.stdout)
        csvf.writerow(['Name', 'Email'])
        for ent in qs:
            csvf.writerow([full_name(**ent), ent['email']])

    def linkedin(self, qs):
        """
        CSV format suitable for importing into linkedin Groups.
        perfect for pre-approving members of a linkedin group.
        """
        csvf = writer(sys.stdout)
        csvf.writerow(['First Name', 'Last Name', 'Email'])
        for ent in qs:
            csvf.writerow([ent['first_name'], ent['last_name'], ent['email']])

    def outlook(self, qs):
        """CSV format suitable for importing into outlook"""
        csvf = writer(sys.stdout)
        columns = ['Name', 'E-mail Address', 'Notes', 'E-mail 2 Address', 'E-mail 3 Address',
                   'Mobile Phone', 'Pager', 'Company', 'Job Title', 'Home Phone', 'Home Phone 2',
                   'Home Fax', 'Home Address', 'Business Phone', 'Business Phone 2',
                   'Business Fax', 'Business Address', 'Other Phone', 'Other Fax', 'Other Address']
        csvf.writerow(columns)
        empty = [''] * (len(columns) - 2)
        for ent in qs:
            csvf.writerow([full_name(**ent), ent['email']] + empty)

    def vcard(self, qs):
        """VCARD format."""
        try:
            import vobject
        except ImportError:
            print(self.style.ERROR("Please install vobject to use the vcard export format."))
            sys.exit(1)

        out = sys.stdout
        for ent in qs:
            card = vobject.vCard()
            card.add('fn').value = full_name(**ent)
            if not ent['last_name'] and not ent['first_name']:
                # fallback to fullname, if both first and lastname are not declared
                card.add('n').value = vobject.vcard.Name(full_name(**ent))
            else:
                card.add('n').value = vobject.vcard.Name(ent['last_name'], ent['first_name'])
            emailpart = card.add('email')
            emailpart.value = ent['email']
            emailpart.type_param = 'INTERNET'

            out.write(card.serialize())
