Current Admin Extensions
========================

:synopsis: Current Field Extensions


* *ForeignKeyAutocompleteAdmin* - ForeignKeyAutocompleteAdmin will enable the
  admin app to show ForeignKey fields with an search input field. The search
  field is rendered by the ForeignKeySearchInput form widget and uses jQuery
  to do configureable autocompletion.


Example Usage
-------------

To enable the Admin Autocomplete you can follow this code example
in your admin.py file:

::

    from django.contrib import admin
    from foo.models import Permission
    from django_extensions.admin import ForeignKeyAutocompleteAdmin


    class PermissionAdmin(ForeignKeyAutocompleteAdmin):
        # User is your FK attribute in your model
        # first_name and email are attributes to search for in the FK model
        related_search_fields = {
           'user': ('first_name', 'email'),
        }

        fields = ('user', 'avatar', 'is_active')

        ...

    admin.site.register(Permission, PermissionAdmin)


If you are using django-reversion you should follow this code example:

::

    from django.contrib import admin
    from foo.models import MyVersionModel
    from reversion.admin import VersionAdmin
    from django_extensions.admin import ForeignKeyAutocompleteAdmin


    class MyVersionModelAdmin(VersionAdmin, ForeignKeyAutocompleteAdmin):
        ...

    admin.site.register(MyVersionModel, MyVersionModelAdmin)
