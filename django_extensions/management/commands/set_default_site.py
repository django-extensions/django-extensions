# -*- coding: utf-8 -*-
import socket

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Set parameters of the default django.contrib.sites Site"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--name", dest="site_name", default=None, help="Use this as site name."
        )
        parser.add_argument(
            "--domain",
            dest="site_domain",
            default=None,
            help="Use this as site domain.",
        )
        parser.add_argument(
            "--system-fqdn",
            dest="set_as_system_fqdn",
            default=False,
            action="store_true",
            help="Use the systems FQDN (Fully Qualified Domain Name) as name "
            "and domain. Can be used in combination with --name",
        )

    @signalcommand
    def handle(self, *args, **options):
        if not apps.is_installed("django.contrib.sites"):
            raise CommandError("The sites framework is not installed.")

        from django.contrib.sites.models import Site

        try:
            site = Site.objects.get(pk=settings.SITE_ID)
        except Site.DoesNotExist:
            raise CommandError(
                "Default site with pk=%s does not exist" % settings.SITE_ID
            )
        else:
            name = options["site_name"]
            domain = options["site_domain"]
            set_as_system_fqdn = options["set_as_system_fqdn"]
            if all([domain, set_as_system_fqdn]):
                raise CommandError(
                    "The set_as_system_fqdn cannot be used with domain option."
                )  # noqa
            if set_as_system_fqdn:
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
                Site.objects.filter(pk=settings.SITE_ID).update(**update_kwargs)
                site = Site.objects.get(pk=settings.SITE_ID)
                print(
                    "Updated default site. You might need to restart django as sites"
                    " are cached aggressively."
                )
            else:
                print("Nothing to update (need --name, --domain and/or --system-fqdn)")

            print("Default Site:")
            print("\tid = %s" % site.id)
            print("\tname = %s" % site.name)
            print("\tdomain = %s" % site.domain)
