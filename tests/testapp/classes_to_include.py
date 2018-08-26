# -*- coding: utf-8 -*-
class BaseIncludedClass:
    pass


class IncludedMixin:
    pass


class FirstDerivedClass(BaseIncludedClass, IncludedMixin):
    pass
