# -*- coding: utf-8 -*-
"""
set_default_site.py
"""
import socket

from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Set parameters of the default django.contrib.sites Site"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--name', dest='site_name', default=None,
                            help='Use this as site name.')
        parser.add_argument('--domain', dest='site_domain', default=None,
                            help='Use this as site domain.')
        parser.add_argument(
            '--system-fqdn', dest='set_as_system_fqdn', default=False,
            action="store_true",
            help='Use the systems FQDN (Fully Qualified Domain Name) as name '
            'and domain. Can be used in combination with --name')

    @signalcommand
    def handle(self, *args, **options):
        from django.contrib.sites.models import Site

        try:
            site = Site.objects.get(pk=1)
        except Site.DoesNotExist:
            raise CommandError("Default site with pk=1 does not exist")
        else:
            name = options.get("site_name", None)
            domain = options.get("site_domain", None)
            if options.get('set_as_system_fqdn', False):
                domain = socket.getfqdn()
                if not domain:
                    raise CommandError("Cannot find systems FQDN")
                if name is None:
                    name = domain

            update_kwargs = {}
            if name and name != site.name:
                update_kwargs["name"] = name

            if domain and domain != site.domain:
                update_kwargs["domain"] = domain

            if update_kwargs:
                Site.objects.filter(pk=1).update(**update_kwargs)
                site = Site.objects.get(pk=1)
                print("Updated default site. You might need to restart django as sites are cached aggressively.")
            else:
                print("Nothing to update (need --name, --domain and/or --system-fqdn)")

            print("Default Site:")
            print("\tid = %s" % site.id)
            print("\tname = %s" % site.name)
            print("\tdomain = %s" % site.domain)
