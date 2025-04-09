# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "List all permissions for models. "
        "By default, excludes admin, auth, contenttypes, and sessions apps."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label_model",
            nargs="*",
            help="[app_label.]model(s) to show permissions for.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Include results for admin, auth, contenttypes, and sessions.",
        )
        parser.add_argument("--app-label", help="App label to dump permissions for.")

    def handle(self, *args, **options):
        app_label_models = options["app_label_model"]
        include_all = options["all"]
        app_label_filter = options["app_label"]

        if include_all:
            content_types = ContentType.objects.order_by("app_label", "model")
        elif app_label_filter:
            content_types = ContentType.objects.filter(
                app_label=app_label_filter.lower()
            ).order_by("app_label", "model")
            if not content_types:
                raise CommandError(
                    f'No content types found for app label "{app_label_filter}".'
                )
        elif not app_label_models:
            excluded = ["admin", "auth", "contenttypes", "sessions"]
            content_types = ContentType.objects.exclude(
                app_label__in=excluded
            ).order_by("app_label", "model")
        else:
            content_types = []
            for value in app_label_models:
                if "." in value:
                    app_label, model = value.split(".")
                    qs = ContentType.objects.filter(app_label=app_label, model=model)
                else:
                    qs = ContentType.objects.filter(model=value)

                if not qs:
                    raise CommandError(f"Content type not found for '{value}'.")
                content_types.extend(qs)

        for ct in content_types:
            self.stdout.write(f"Permissions for {ct}")
            for perm in ct.permission_set.all():
                self.stdout.write(f"    {ct.app_label}.{perm.codename} | {perm.name}")
