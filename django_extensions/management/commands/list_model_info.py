# -*- coding: utf-8 -*-
# Author: OmenApps. http://www.omenapps.com
import inspect

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django_extensions.management.color import color_style
from django_extensions.management.utils import signalcommand

TAB = "        "
HALFTAB = "    "


class Command(BaseCommand):
    """A simple management command which lists model fields and methods."""

    help = "List out the fields and methods for each model"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--field-class", action="store_true", default=None, help="show class name of field.")
        parser.add_argument("--db-type", action="store_true", default=None, help="show database column type of field.")
        parser.add_argument("--signature", action="store_true", default=None, help="show the signature of method.")
        parser.add_argument(
            "--all-methods", action="store_true", default=None, help="list all methods, including private and default."
        )
        parser.add_argument(
            "--model",
            nargs="?",
            type=str,
            default=None,
            help="list the details for a single model. Input should be in the form appname.Modelname",
        )

    def list_model_info(self, options):

        style = color_style()
        INFO = getattr(style, "INFO", lambda x: x)
        WARN = getattr(style, "WARN", lambda x: x)
        BOLD = getattr(style, "BOLD", lambda x: x)

        FIELD_CLASS = (
            True if options.get("field_class", None) is not None else getattr(settings, "MODEL_INFO_FIELD_CLASS", False)
        )
        DB_TYPE = True if options.get("db_type", None) is not None else getattr(settings, "MODEL_INFO_DB_TYPE", False)
        SIGNATURE = (
            True if options.get("signature", None) is not None else getattr(settings, "MODEL_INFO_SIGNATURE", False)
        )
        ALL_METHODS = (
            True if options.get("all_methods", None) is not None else getattr(settings, "MODEL_INFO_ALL_METHODS", False)
        )
        MODEL = (
            options.get("model")
            if options.get("model", None) is not None
            else getattr(settings, "MODEL_INFO_MODEL", False)
        )

        default_methods = [
            "check",
            "clean",
            "clean_fields",
            "date_error_message",
            "delete",
            "from_db",
            "full_clean",
            "get_absolute_url",
            "get_deferred_fields",
            "prepare_database_save",
            "refresh_from_db",
            "save",
            "save_base",
            "serializable_value",
            "unique_error_message",
            "validate_unique",
        ]

        if MODEL:
            model_list = [django_apps.get_model(MODEL)]
        else:
            model_list = sorted(
                django_apps.get_models(), key=lambda x: (x._meta.app_label, x._meta.object_name), reverse=False
            )
        for model in model_list:
            self.stdout.write(INFO(model._meta.app_label + "." + model._meta.object_name))
            self.stdout.write(BOLD(HALFTAB + "Fields:"))

            for field in model._meta.get_fields():
                field_info = TAB + field.name + " -"

                if FIELD_CLASS:
                    try:
                        field_info += " " + field.__class__.__name__
                    except TypeError:
                        field_info += (WARN(" TypeError (field_class)"))
                    except AttributeError:
                        field_info += (WARN(" AttributeError (field_class)"))
                if FIELD_CLASS and DB_TYPE:
                    field_info += ","
                if DB_TYPE:
                    try:
                        field_info += " " + field.db_type(connection=connection)
                    except TypeError:
                        field_info += (WARN(" TypeError (db_type)"))
                    except AttributeError:
                        field_info += (WARN(" AttributeError (db_type)"))

                self.stdout.write(field_info)

            if ALL_METHODS:
                self.stdout.write(BOLD(HALFTAB + "Methods (all):"))
            else:
                self.stdout.write(BOLD(HALFTAB + "Methods (non-private/internal):"))

            for method_name in dir(model):
                try:
                    method = getattr(model, method_name)
                    if ALL_METHODS:
                        if callable(method) and not method_name[0].isupper():
                            if SIGNATURE:
                                signature = inspect.signature(method)
                            else:
                                signature = "()"
                            self.stdout.write(TAB + method_name + str(signature))
                    else:
                        if (
                            callable(method)
                            and not method_name.startswith("_")
                            and method_name not in default_methods
                            and not method_name[0].isupper()
                        ):
                            if SIGNATURE:
                                signature = inspect.signature(method)
                            else:
                                signature = "()"
                            self.stdout.write(TAB + method_name + str(signature))
                except AttributeError:
                    self.stdout.write(TAB + method_name + WARN(" - AttributeError"))
                except ValueError:
                    self.stdout.write(TAB + method_name + WARN(" - ValueError (could not identify signature)"))

            self.stdout.write("\n")

        self.stdout.write(INFO("Total Models Listed: %d" % len(model_list)))

    @signalcommand
    def handle(self, *args, **options):
        self.list_model_info(options)
