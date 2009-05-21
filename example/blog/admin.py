from django.contrib import admin
from example.blog.models import Entry
from django_extensions.admin import ForeignKeyAutocompleteAdmin

class EntryAdmin(ForeignKeyAutocompleteAdmin):
    related_search_fields = {
       'author': ('first_name', 'email'),
    }
admin.site.register(Entry, EntryAdmin)
