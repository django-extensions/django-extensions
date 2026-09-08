import datetime
from pathlib import Path

from django.template.engine import Engine
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "List template search paths."

    def handle(self, *args, **options):

        test_template_name = "this_template_name_should_not_exist"

        engine = Engine.get_default()
        try:
            engine.find_template(test_template_name)
        except Exception as e:
            unique_paths = []
            for path in e.tried:
                parent = Path(path[0].name).parent
                if parent not in unique_paths:
                    unique_paths.append(parent)
            self.stdout.write("\n".join(str(x) for x in unique_paths))
