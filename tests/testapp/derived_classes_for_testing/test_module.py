# -*- coding: utf-8 -*-
from tests.testapp.classes_to_include import IncludedMixin


class ClassWhichShouldNotBeImported:
    pass


class ThirdDerivedClass(IncludedMixin):
    pass
