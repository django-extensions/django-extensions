# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys

from django.conf import settings
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


def full_name(**kwargs):
    """Return full name or username."""
    first_name = kwargs.get('first_name')
    last_name = kwargs.get('last_name')

    name = " ".join(n for n in [first_name, last_name] if n)
    if name:
        return name

    name = kwargs.get('name')
    if name:
        return name

    username = kwargs.get('username')
    if username:
        return username

    return ""


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

    def full_name(self, **kwargs):
        return getattr(settings, 'EXPORT_EMAILS_FULL_NAME_FUNC', full_name)(**kwargs)

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
        order_by = getattr(settings, 'EXPORT_EMAILS_ORDER_BY', ['last_name', 'first_name', 'username', 'email'])
        fields = getattr(settings, 'EXPORT_EMAILS_FIELDS', ['last_name', 'first_name', 'username', 'email'])

        qs = UserModel.objects.all().order_by(*order_by)
        if group:
            qs = qs.filter(groups__name=group).distinct()
        qs = qs.values(*fields)
        getattr(self, options['format'])(qs)

    def address(self, qs):
        """
        Single entry per line in the format of:
            "full name" <my@address.com>;
        """
        self.stdout.write("\n".join('"%s" <%s>;' % (self.full_name(**ent), ent.get('email', '')) for ent in qs))
        self.stdout.write("\n")

    def emails(self, qs):
        """
        Single entry with email only in the format of:
            my@address.com,
        """
        self.stdout.write(",\n".join(ent['email'] for ent in qs if ent.get('email')))
        self.stdout.write("\n")

    def google(self, qs):
        """CSV format suitable for importing into google GMail"""
        csvf = writer(sys.stdout)
        csvf.writerow(['Name', 'Email'])
        for ent in qs:
            csvf.writerow([self.full_name(**ent), ent.get('email', '')])

    def linkedin(self, qs):
        """
        CSV format suitable for importing into linkedin Groups.
        perfect for pre-approving members of a linkedin group.
        """
        csvf = writer(sys.stdout)
        csvf.writerow(['First Name', 'Last Name', 'Email'])
        for ent in qs:
            csvf.writerow([ent.get('first_name', ''), ent.get('last_name', ''), ent.get('email', '')])

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
            csvf.writerow([self.full_name(**ent), ent.get('email', '')] + empty)

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
            card.add('fn').value = self.full_name(**ent)
            if ent.get('last_name') and ent.get('first_name'):
                card.add('n').value = vobject.vcard.Name(ent['last_name'], ent['first_name'])
            else:
                # fallback to fullname, if both first and lastname are not declared
                card.add('n').value = vobject.vcard.Name(self.full_name(**ent))
            if ent.get('email'):
                emailpart = card.add('email')
                emailpart.value = ent['email']
                emailpart.type_param = 'INTERNET'

            out.write(card.serialize())
