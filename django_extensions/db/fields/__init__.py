"""
Django Extensions additional model fields
"""
import re
import six
import string
import warnings

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

from django.core.exceptions import ImproperlyConfigured
from django.db.models import DateTimeField, CharField, SlugField
from django.utils.crypto import get_random_string
from django.template.defaultfilters import slugify

try:
    from django.utils.timezone import now as datetime_now
    assert datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now

try:
    from django.utils.encoding import force_unicode  # NOQA
except ImportError:
    from django.utils.encoding import force_text as force_unicode  # NOQA


MAX_UNIQUE_QUERY_ATTEMPTS = 100


class UniqueFieldMixin(object):

    def check_is_bool(self, attrname):
        if not isinstance(getattr(self, attrname), bool):
            raise ValueError("'{}' argument must be True or False".format(attrname))

    def get_queryset(self, model_cls, slug_field):
        for field, model in model_cls._meta.get_fields_with_model():
            if model and field == slug_field:
                return model._default_manager.all()
        return model_cls._default_manager.all()

    def find_unique(self, model_instance, field, iterator, *args):
        # exclude the current model instance from the queryset used in finding
        # next valid hash
        queryset = self.get_queryset(model_instance.__class__, field)
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to impliment any unique_together contraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)

        new = six.next(iterator)
        kwargs[self.attname] = new
        while not new or queryset.filter(**kwargs):
            new = six.next(iterator)
            kwargs[self.attname] = new
        setattr(model_instance, self.attname, new)
        return new


class AutoSlugField(UniqueFieldMixin, SlugField):
    """ AutoSlugField

    By default, sets editable=False, blank=True.

    Required arguments:

    populate_from
        Specifies which field or list of fields the slug is populated from.

    Optional arguments:

    separator
        Defines the used separator (default: '-')

    overwrite
        If set to True, overwrites the slug on every save (default: False)

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

        self.slugify_function = kwargs.pop('slugify_function', slugify)
        self.separator = kwargs.pop('separator', six.u('-'))
        self.overwrite = kwargs.pop('overwrite', False)
        self.check_is_bool('overwrite')
        self.allow_duplicates = kwargs.pop('allow_duplicates', False)
        self.check_is_bool('allow_duplicates')
        super(AutoSlugField, self).__init__(*args, **kwargs)

    def _slug_strip(self, value):
        """
        Cleans up a slug by removing slug separator characters that occur at
        the beginning or end of a slug.

        If an alternate separator is used, it will also replace any instances
        of the default '-' separator with the new separator.
        """
        re_sep = '(?:-|%s)' % re.escape(self.separator)
        value = re.sub('%s+' % re_sep, self.separator, value)
        return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)

    def slugify_func(self, content):
        if content:
            return self.slugify_function(content)
        return ''

    def slug_generator(self, original_slug, start):
        yield original_slug
        for i in range(start, MAX_UNIQUE_QUERY_ATTEMPTS):
            slug = original_slug
            end = '%s%s' % (self.separator, i)
            end_len = len(end)
            if self.slug_len and len(slug) + end_len > self.slug_len:
                slug = slug[:self.slug_len - end_len]
                slug = self._slug_strip(slug)
            slug = '%s%s' % (slug, end)
            yield slug
        raise RuntimeError('max slug attempts for %s exceeded (%s)' %
            (original_slug, MAX_UNIQUE_QUERY_ATTEMPTS))

    def create_slug(self, model_instance, add):
        # get fields to populate from and slug field to set
        if not isinstance(self._populate_from, (list, tuple)):
            self._populate_from = (self._populate_from, )
        slug_field = model_instance._meta.get_field(self.attname)

        if add or self.overwrite:
            # slugify the original field content and set next step to 2
            slug_for_field = lambda field: self.slugify_func(getattr(model_instance, field))
            slug = self.separator.join(map(slug_for_field, self._populate_from))
            start = 2
        else:
            # get slug from the current model instance
            slug = getattr(model_instance, self.attname)
            # model_instance is being modified, and overwrite is False,
            # so instead of doing anything, just return the current slug
            return slug

        # strip slug depending on max_length attribute of the slug field
        # and clean-up
        self.slug_len = slug_field.max_length
        if self.slug_len:
            slug = slug[:self.slug_len]
        slug = self._slug_strip(slug)
        original_slug = slug

        if self.allow_duplicates:
            return slug

        return super(AutoSlugField, self).find_unique(
            model_instance, slug_field, self.slug_generator(original_slug, start))

    def pre_save(self, model_instance, add):
        value = force_unicode(self.create_slug(model_instance, add))
        return value

    def get_internal_type(self):
        return "SlugField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = '%s.AutoSlugField' % self.__module__
        args, kwargs = introspector(self)
        kwargs.update({
            'populate_from': repr(self._populate_from),
            'separator': repr(self.separator),
            'overwrite': repr(self.overwrite),
            'allow_duplicates': repr(self.allow_duplicates),
        })
        # That's our definition!
        return (field_class, args, kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(AutoSlugField, self).deconstruct()
        kwargs['populate_from'] = self._populate_from
        if not self.separator == six.u('-'):
            kwargs['separator'] = self.separator
        if self.overwrite is not False:
            kwargs['overwrite'] = True
        if self.allow_duplicates is not False:
            kwargs['allow_duplicates'] = True
        return name, path, args, kwargs


class RandomCharField(UniqueFieldMixin, CharField):
    """ RandomCharField

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

        # Set unique=False unless it's been set manually.
        if 'unique' not in kwargs:
            kwargs['unique'] = False

        super(RandomCharField, self).__init__(*args, **kwargs)

    def random_char_generator(self, chars):
        for i in range(MAX_UNIQUE_QUERY_ATTEMPTS):
            yield ''.join(get_random_string(self.length, chars))
        raise RuntimeError('max random character attempts exceeded (%s)' %
            MAX_UNIQUE_QUERY_ATTEMPTS)

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
        if not self.unique:
            return random_chars

        return super(RandomCharField, self).find_unique(
            model_instance,
            model_instance._meta.get_field(self.attname),
            random_chars,
        )

    def internal_type(self):
        return "CharField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = '%s.RandomCharField' % self.__module__
        args, kwargs = introspector(self)
        kwargs.update({
            'lowercase': repr(self.lowercase),
            'include_digits': repr(self.include_digits),
            'include_aphla': repr(self.include_alpha),
            'include_punctuation': repr(self.include_punctuation),
            'length': repr(self.length),
            'unique': repr(self.unique),
        })
        del kwargs['max_length']
        # That's our definition!
        return (field_class, args, kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(RandomCharField, self).deconstruct()
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
    """ CreationDateTimeField

    By default, sets editable=False, blank=True, auto_now_add=True
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('auto_now_add', True)
        DateTimeField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.DateTimeField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CreationDateTimeField, self).deconstruct()
        if self.editable is not False:
            kwargs['editable'] = True
        if self.blank is not True:
            kwargs['blank'] = False
        if self.auto_now_add is not False:
            kwargs['auto_now_add'] = True
        return name, path, args, kwargs


class ModificationDateTimeField(CreationDateTimeField):
    """ ModificationDateTimeField

    By default, sets editable=False, blank=True, auto_now=True

    Sets value to now every time the object is saved.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now', True)
        DateTimeField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.DateTimeField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ModificationDateTimeField, self).deconstruct()
        if self.auto_now is not False:
            kwargs['auto_now'] = True
        return name, path, args, kwargs


class UUIDVersionError(Exception):
    pass


class UUIDField(CharField):
    """ UUIDField

    By default uses UUID version 4 (randomly generated UUID).

    The field support all uuid versions which are natively supported by the uuid python module, except version 2.
    For more information see: http://docs.python.org/lib/module-uuid.html
    """
    DEFAULT_MAX_LENGTH = 36

    def __init__(self, verbose_name=None, name=None, auto=True, version=4, node=None, clock_seq=None, namespace=None, uuid_name=None, *args, **kwargs):
        warnings.warn("Django 1.8 features a native UUIDField, this UUIDField will be removed after Django 1.7 becomes unsupported.", DeprecationWarning)

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
        super(UUIDField, self).__init__(verbose_name=verbose_name, *args, **kwargs)

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
        value = super(UUIDField, self).pre_save(model_instance, add)
        if self.auto and add and value is None:
            value = force_unicode(self.create_uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            if self.auto and not value:
                value = force_unicode(self.create_uuid())
                setattr(model_instance, self.attname, value)
        return value

    def formfield(self, **kwargs):
        if self.auto:
            return None
        return super(UUIDField, self).formfield(**kwargs)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(UUIDField, self).deconstruct()
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


class PostgreSQLUUIDField(UUIDField):
    def __init__(self, *args, **kwargs):
        warnings.warn("Django 1.8 features a native UUIDField, this UUIDField will be removed after Django 1.7 becomes unsupported.", DeprecationWarning)
        super(PostgreSQLUUIDField, self).__init__(*args, **kwargs)

    def db_type(self, connection=None):
        return "UUID"

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, six.integer_types):
            value = uuid.UUID(int=value)
        elif isinstance(value, (six.string_types, six.binary_type)):
            if len(value) == 16:
                value = uuid.UUID(bytes=value)
            else:
                value = uuid.UUID(value)
        return super(PostgreSQLUUIDField, self).get_db_prep_value(
            value, connection, prepared=False)


class ShortUUIDField(UUIDField):
    """ ShortUUIDFied

    Generates concise (22 characters instead of 36), unambiguous, URL-safe UUIDs.

    Based on `shortuuid`: https://github.com/stochastic-technologies/shortuuid
    """
    DEFAULT_MAX_LENGTH = 22

    def __init__(self, *args, **kwargs):
        super(ShortUUIDField, self).__init__(*args, **kwargs)
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
