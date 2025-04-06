# -*- coding: utf-8 -*-
from django.apps import apps as django_apps
from django.contrib.auth.management import create_permissions
from django.contrib.auth.management import _get_all_permissions  # type: ignore
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = (
        "reloads permissions for specified apps, or all apps if no args are specified"
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--apps",
            dest="apps",
            help="Reload permissions only for apps (comma separated)",
        )
        parser.add_argument(
            "--create-only",
            action="store_true",
            default=False,
            help="Only create missing permissions",
        )
        parser.add_argument(
            "--update-only",
            action="store_true",
            default=False,
            help="Only update permissions",
        )

    @signalcommand
    def handle(self, *args, **options):
        if options["apps"]:
            app_names = options["apps"].split(",")
            apps = [django_apps.get_app_config(x) for x in app_names]
        else:
            apps = django_apps.get_app_configs()

        if options["create_only"]:
            do_create, do_update = True, False
        elif options["update_only"]:
            do_create, do_update = False, True
        else:
            do_create, do_update = True, True

        for app in apps:
            if do_create:
                # create permissions if they do not exist
                create_permissions(app, options["verbosity"])

            if do_update:
                # update permission name's if changed
                for model in app.get_models():
                    content_type = ContentType.objects.get_for_model(model)
                    for codename, name in _get_all_permissions(model._meta):
                        try:
                            permission = Permission.objects.get(
                                codename=codename, content_type=content_type
                            )
                        except Permission.DoesNotExist:
                            continue
                        if permission.name != name:
                            old_str = str(permission)
                            permission.name = name
                            if options["verbosity"] >= 2:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        "Update permission '%s' to '%s'"
                                        % (old_str, permission)
                                    )
                                )
                            permission.save()
