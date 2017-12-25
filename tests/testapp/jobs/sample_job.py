# -*- coding: utf-8 -*-
from django_extensions.management.jobs import BaseJob


class Job(BaseJob):
    help = "My sample job."

    def execute(self):
        print("executing empty sample job")
