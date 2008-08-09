"""
Django Extensions additional model fields
"""

from django.db.models import DateTimeField
import datetime

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
