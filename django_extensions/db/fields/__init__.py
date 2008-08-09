"""
Django Extensions additional model fields
"""

from django.db.models import DateTimeField, CharField
import datetime

try:
    import uuid
except ImportError:
    from django_extensions.utils import uuid

class CreationDateTimeField(DateTimeField):
    """ CreationDateTimeField """
    
    def __init__(self, *args, **kwargs):
	if not 'editable' in kwargs:
	    kwargs['editable'] = False
	if not 'blank' in kwargs:
	    kwargs['blank'] = True
	DateTimeField.__init__(self, *args, **kwargs)
    
    def pre_save(self, model, add):
	if add or getattr(model, self.attname) is None:
	    value = datetime.datetime.now()
	    setattr(model, self.attname, value)
	    return value
	return super(CreationDateTimeField, self).pre_save(model, add)
    
    def get_internal_type(self):
	return "DateTimeField"

class ModificationDateTimeField(DateTimeField):
    """ CreationDateTimeField """
    
    def __init__(self, *args, **kwargs):
	if not 'editable' in kwargs:
	    kwargs['editable'] = False
	if not 'blank' in kwargs:
	    kwargs['blank'] = True
	DateTimeField.__init__(self, *args, **kwargs)
    
    def pre_save(self, model, add):
	value = datetime.datetime.now()
	setattr(model, self.attname, value)
	return value
    
    def get_internal_type(self):
	return "DateTimeField"

class UUIDVersionError(Exception):
    pass

class UUIDField(CharField):
    """ UUIDField for Django, supports all uuid versions which are natively
        supported by the uuid python module.
    """

    def __init__(self, verbose_name=None, name=None, auto=True, version=1, node=None, clock_seq=None, namespace=None, **kwargs):
        kwargs['maxlength'] = 36
        if auto:
            kwargs['blank'] = True
            kwargs['editable'] = kwargs.get('editable', False)
        self.version = version
        if version==1:
            self.node, self.clock_seq = node, clock_seq
        elif version==3 or version==5:
            self.namespace, self.name = namespace, name
        CharField.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return CharField.__name__

    def create_uuid(self):
        if not self.version or self.version==4:
            return uuid.uuid4()
        elif self.version==1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version==2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version==3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version==5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)

    def pre_save(self, model_instance, add):
        if self.auto and add:
            value = unicode(self.create_uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            value = super(UUIDField, self).pre_save(model_instance, add)
            if self.auto and not value:
                value = unicode(self.create_uuid())
                setattr(model_instance, self.attname, value)
        return value

