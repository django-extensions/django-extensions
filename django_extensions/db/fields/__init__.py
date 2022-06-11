# -*- coding: utf-8 -*-
"""
Django Extensions additional model fields

Some fields might require additional dependencies to be installed.
"""

import re
import string

try:
    import uuid
    HAS_UUID = True
except ImportError:
    HAS_UUID = False

try:
    import shortuuid
    HAS_SHORT_UUID = True
except ImportError:
    HAS_SHORT_UUID = False

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import DateTimeField, CharField, SlugField, Q, UniqueConstraint
from django.db.models.constants import LOOKUP_SEP
from django.template.defaultfilters import slugify
from django.utils.crypto import get_random_string
from django.utils.encoding import force_str


MAX_UNIQUE_QUERY_ATTEMPTS = getattr(settings, 'EXTENSIONS_MAX_UNIQUE_QUERY_ATTEMPTS', 100)


class UniqueFieldMixin:

    def check_is_bool(self, attrname):
        if not isinstance(getattr(self, attrname), bool):
            raise ValueError("'{}' argument must be True or False".format(attrname))

    @staticmethod
    def _get_fields(model_cls):
        return [
            (f, f.model if f.model != model_cls else None) for f in model_cls._meta.get_fields()
            if not f.is_relation or f.one_to_one or (f.many_to_one and f.related_model)
        ]

    def get_queryset(self, model_cls, slug_field):
        for field, model in self._get_fields(model_cls):
            if model and field == slug_field:
                return model._default_manager.all()
        return model_cls._default_manager.all()

    def find_unique(self, model_instance, field, iterator, *args):
        # exclude the current model instance from the queryset used in finding
        # next valid hash
        queryset = self.get_queryset(model_instance.__class__, field)
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to implement any unique_together constraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)

        # for support django 2.2+
        query = Q()
        constraints = getattr(model_instance._meta, 'constraints', None)
        if constraints:
            unique_constraints = filter(
                lambda c: isinstance(c, UniqueConstraint), constraints
            )
            for unique_constraint in unique_constraints:
                if self.attname in unique_constraint.fields:
                    condition = {
                        field: getattr(model_instance, field, None)
                        for field in unique_constraint.fields
                        if field != self.attname
                    }
                    query &= Q(**condition)

        new = next(iterator)
        kwargs[self.attname] = new
        while not new or queryset.filter(query, **kwargs):
            new = next(iterator)
            kwargs[self.attname] = new
        setattr(model_instance, self.attname, new)
        return new


class AutoSlugField(UniqueFieldMixin, SlugField):
    """
    AutoSlugField

    By default, sets editable=False, blank=True.

    Required arguments:

    populate_from
        Specifies which field, list of fields, or model method
        the slug will be populated from.

        populate_from can traverse a ForeignKey relationship
        by using Django ORM syntax:
            populate_from = 'related_model__field'

    Optional arguments:

    separator
        Defines the used separator (default: '-')

    overwrite
        If set to True, overwrites the slug on every save (default: False)

    slugify_function
        Defines the function which will be used to "slugify" a content
        (default: :py:func:`~django.template.defaultfilters.slugify` )

    It is possible to provide custom "slugify" function with
    the ``slugify_function`` function in a model class.

    ``slugify_function`` function in a model class takes priority over
    ``slugify_function`` given as an argument to :py:class:`~AutoSlugField`.

    Example

    .. code-block:: python

        # models.py

        from django.db import models

        from django_extensions.db.fields import AutoSlugField


        class MyModel(models.Model):
            def slugify_function(self, content):
                return content.replace('_', '-').lower()

            title = models.CharField(max_length=42)
            slug = AutoSlugField(populate_from='title')

    Inspired by SmileyChris' Unique Slugify snippet:
    http://www.djangosnippets.org/snippets/690/
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', False)

        populate_from = kwargs.pop('populate_from', None)
        if populate_from is None:
            raise ValueError("missing 'populate_from' argument")
        else:
            self._populate_from = populate_from

        if not callable(populate_from):
            if not isinstance(populate_from, (list, tuple)):
                populate_from = (populate_from, )

            if not all(isinstance(e, str) for e in populate_from):
                raise TypeError("'populate_from' must be str or list[str] or tuple[str], found `%s`" % populate_from)

        self.slugify_function = kwargs.pop('slugify_function', slugify)
        self.separator = kwargs.pop('separator', '-')
        self.overwrite = kwargs.pop('overwrite', False)
        self.check_is_bool('overwrite')
        self.overwrite_on_add = kwargs.pop('overwrite_on_add', True)
        self.check_is_bool('overwrite_on_add')
        self.allow_duplicates = kwargs.pop('allow_duplicates', False)
        self.check_is_bool('allow_duplicates')
        self.max_unique_query_attempts = kwargs.pop('max_unique_query_attempts', MAX_UNIQUE_QUERY_ATTEMPTS)
        super().__init__(*args, **kwargs)

    def _slug_strip(self, value):
        """
        Clean up a slug by removing slug separator characters that occur at
        the beginning or end of a slug.

        If an alternate separator is used, it will also replace any instances
        of the default '-' separator with the new separator.
        """
        re_sep = '(?:-|%s)' % re.escape(self.separator)
        value = re.sub('%s+' % re_sep, self.separator, value)
        return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)

    @staticmethod
    def slugify_func(content, slugify_function):
        if content:
            return slugify_function(content)
        return ''

    def slug_generator(self, original_slug, start):
        yield original_slug
        for i in range(start, self.max_unique_query_attempts):
            slug = original_slug
            end = '%s%s' % (self.separator, i)
            end_len = len(end)
            if self.slug_len and len(slug) + end_len > self.slug_len:
                slug = slug[:self.slug_len - end_len]
                slug = self._slug_strip(slug)
            slug = '%s%s' % (slug, end)
            yield slug
        raise RuntimeError('max slug attempts for %s exceeded (%s)' % (original_slug, self.max_unique_query_attempts))

    def create_slug(self, model_instance, add):
        slug = getattr(model_instance, self.attname)
        use_existing_slug = False
        if slug and not self.overwrite:
            # Existing slug and not configured to overwrite - Short-circuit
            # here to prevent slug generation when not required.
            use_existing_slug = True

        if self.overwrite_on_add and add:
            use_existing_slug = False

        if use_existing_slug:
            return slug

        # get fields to populate from and slug field to set
        populate_from = self._populate_from
        if not isinstance(populate_from, (list, tuple)):
            populate_from = (populate_from, )

        slug_field = model_instance._meta.get_field(self.attname)
        slugify_function = getattr(model_instance, 'slugify_function', self.slugify_function)

        # slugify the original field content and set next step to 2
        slug_for_field = lambda lookup_value: self.slugify_func(
            self.get_slug_fields(model_instance, lookup_value),
            slugify_function=slugify_function
        )
        slug = self.separator.join(map(slug_for_field, populate_from))
        start = 2

        # strip slug depending on max_length attribute of the slug field
        # and clean-up
        self.slug_len = slug_field.max_length
        if self.slug_len:
            slug = slug[:self.slug_len]
        slug = self._slug_strip(slug)
        original_slug = slug

        if self.allow_duplicates:
            setattr(model_instance, self.attname, slug)
            return slug

        return self.find_unique(
            model_instance, slug_field, self.slug_generator(original_slug, start))

    def get_slug_fields(self, model_instance, lookup_value):
        if callable(lookup_value):
            # A function has been provided
            return "%s" % lookup_value(model_instance)

        lookup_value_path = lookup_value.split(LOOKUP_SEP)
        attr = model_instance
        for elem in lookup_value_path:
            try:
                attr = getattr(attr, elem)
            except AttributeError:
                raise AttributeError(
                    "value {} in AutoSlugField's 'populate_from' argument {} returned an error - {} has no attribute {}".format(
                        elem, lookup_value, attr, elem))

        if callable(attr):
            return "%s" % attr()

        return attr

    def pre_save(self, model_instance, add):
        value = force_str(self.create_slug(model_instance, add))
        return value

    def get_internal_type(self):
        return "SlugField"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['populate_from'] = self._populate_from
        if not self.separator == '-':
            kwargs['separator'] = self.separator
        if self.overwrite is not False:
            kwargs['overwrite'] = True
        if self.allow_duplicates is not False:
            kwargs['allow_duplicates'] = True
        return name, path, args, kwargs


class RandomCharField(UniqueFieldMixin, CharField):
    """
    RandomCharField

    By default, sets editable=False, blank=True, unique=False.

    Required arguments:

    length
        Specifies the length of the field

    Optional arguments:

    unique
        If set to True, duplicate entries are not allowed (default: False)

    lowercase
        If set to True, lowercase the alpha characters (default: False)

    uppercase
        If set to True, uppercase the alpha characters (default: False)

    include_alpha
        If set to True, include alpha characters (default: True)

    include_digits
        If set to True, include digit characters (default: True)

    include_punctuation
        If set to True, include punctuation characters (default: False)
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', False)

        self.length = kwargs.pop('length', None)
        if self.length is None:
            raise ValueError("missing 'length' argument")
        kwargs['max_length'] = self.length

        self.lowercase = kwargs.pop('lowercase', False)
        self.check_is_bool('lowercase')
        self.uppercase = kwargs.pop('uppercase', False)
        self.check_is_bool('uppercase')
        if self.uppercase and self.lowercase:
            raise ValueError("the 'lowercase' and 'uppercase' arguments are mutually exclusive")
        self.include_digits = kwargs.pop('include_digits', True)
        self.check_is_bool('include_digits')
        self.include_alpha = kwargs.pop('include_alpha', True)
        self.check_is_bool('include_alpha')
        self.include_punctuation = kwargs.pop('include_punctuation', False)
        self.check_is_bool('include_punctuation')
        self.max_unique_query_attempts = kwargs.pop('max_unique_query_attempts', MAX_UNIQUE_QUERY_ATTEMPTS)

        # Set unique=False unless it's been set manually.
        if 'unique' not in kwargs:
            kwargs['unique'] = False

        super().__init__(*args, **kwargs)

    def random_char_generator(self, chars):
        for i in range(self.max_unique_query_attempts):
            yield ''.join(get_random_string(self.length, chars))
        raise RuntimeError('max random character attempts exceeded (%s)' % self.max_unique_query_attempts)

    def in_unique_together(self, model_instance):
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                return True
        return False

    def pre_save(self, model_instance, add):
        if not add and getattr(model_instance, self.attname) != '':
            return getattr(model_instance, self.attname)

        population = ''
        if self.include_alpha:
            if self.lowercase:
                population += string.ascii_lowercase
            elif self.uppercase:
                population += string.ascii_uppercase
            else:
                population += string.ascii_letters

        if self.include_digits:
            population += string.digits

        if self.include_punctuation:
            population += string.punctuation

        random_chars = self.random_char_generator(population)
        if not self.unique and not self.in_unique_together(model_instance):
            new = next(random_chars)
            setattr(model_instance, self.attname, new)
            return new

        return self.find_unique(
            model_instance,
            model_instance._meta.get_field(self.attname),
            random_chars,
        )

    def internal_type(self):
        return "CharField"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['length'] = self.length
        del kwargs['max_length']
        if self.lowercase is True:
            kwargs['lowercase'] = self.lowercase
        if self.uppercase is True:
            kwargs['uppercase'] = self.uppercase
        if self.include_alpha is False:
            kwargs['include_alpha'] = self.include_alpha
        if self.include_digits is False:
            kwargs['include_digits'] = self.include_digits
        if self.include_punctuation is True:
            kwargs['include_punctuation'] = self.include_punctuation
        if self.unique is True:
            kwargs['unique'] = self.unique
        return name, path, args, kwargs


class CreationDateTimeField(DateTimeField):
    """
    CreationDateTimeField

    By default, sets editable=False, blank=True, auto_now_add=True
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('auto_now_add', True)
        DateTimeField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.editable is not False:
            kwargs['editable'] = True
        if self.blank is not True:
            kwargs['blank'] = False
        if self.auto_now_add is not False:
            kwargs['auto_now_add'] = True
        return name, path, args, kwargs


class ModificationDateTimeField(CreationDateTimeField):
    """
    ModificationDateTimeField

    By default, sets editable=False, blank=True, auto_now=True

    Sets value to now every time the object is saved.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now', True)
        DateTimeField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.auto_now is not False:
            kwargs['auto_now'] = True
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        if not getattr(model_instance, 'update_modified', True):
            return getattr(model_instance, self.attname)
        return super().pre_save(model_instance, add)


class UUIDVersionError(Exception):
    pass


class UUIDFieldMixin:
    """
    UUIDFieldMixin

    By default uses UUID version 4 (randomly generated UUID).

    The field support all uuid versions which are natively supported by the uuid python module, except version 2.
    For more information see: http://docs.python.org/lib/module-uuid.html
    """

    DEFAULT_MAX_LENGTH = 36

    def __init__(self, verbose_name=None, name=None, auto=True, version=4,
                 node=None, clock_seq=None, namespace=None, uuid_name=None, *args,
                 **kwargs):
        if not HAS_UUID:
            raise ImproperlyConfigured("'uuid' module is required for UUIDField. (Do you have Python 2.5 or higher installed ?)")

        kwargs.setdefault('max_length', self.DEFAULT_MAX_LENGTH)

        if auto:
            self.empty_strings_allowed = False
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)

        self.auto = auto
        self.version = version
        self.node = node
        self.clock_seq = clock_seq
        self.namespace = namespace
        self.uuid_name = uuid_name or name

        super().__init__(verbose_name=verbose_name, *args, **kwargs)

    def create_uuid(self):
        if not self.version or self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.uuid_name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.uuid_name)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)

        if self.auto and add and value is None:
            value = force_str(self.create_uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            if self.auto and not value:
                value = force_str(self.create_uuid())
                setattr(model_instance, self.attname, value)

        return value

    def formfield(self, **kwargs):
        if self.auto:
            return None
        return super().formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()

        if kwargs.get('max_length', None) == self.DEFAULT_MAX_LENGTH:
            del kwargs['max_length']
        if self.auto is not True:
            kwargs['auto'] = self.auto
        if self.version != 4:
            kwargs['version'] = self.version
        if self.node is not None:
            kwargs['node'] = self.node
        if self.clock_seq is not None:
            kwargs['clock_seq'] = self.clock_seq
        if self.namespace is not None:
            kwargs['namespace'] = self.namespace
        if self.uuid_name is not None:
            kwargs['uuid_name'] = self.name

        return name, path, args, kwargs


class ShortUUIDField(UUIDFieldMixin, CharField):
    """
    ShortUUIDFied

    Generates concise (22 characters instead of 36), unambiguous, URL-safe UUIDs.

    Based on `shortuuid`: https://github.com/stochastic-technologies/shortuuid
    """

    DEFAULT_MAX_LENGTH = 22

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not HAS_SHORT_UUID:
            raise ImproperlyConfigured("'shortuuid' module is required for ShortUUIDField. (Do you have Python 2.5 or higher installed ?)")
        kwargs.setdefault('max_length', self.DEFAULT_MAX_LENGTH)

    def create_uuid(self):
        if not self.version or self.version == 4:
            return shortuuid.uuid()
        elif self.version == 1:
            return shortuuid.uuid()
        elif self.version == 2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            raise UUIDVersionError("UUID version 3 is not supported.")
        elif self.version == 5:
            return shortuuid.uuid(name=self.namespace)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)
