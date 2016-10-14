Current Admin Extensions
========================

:synopsis: Current Field Extensions


* *ForeignKeyAutocompleteAdmin* - ForeignKeyAutocompleteAdmin will enable the
  admin app to show ForeignKey fields with an search input field. The search
  field is rendered by the ForeignKeySearchInput form widget and uses jQuery
  to do configurable autocompletion.


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

If you need to limit the autocomplete search, you can override the
``get_related_filter`` method of the admin. For example if you want to allow
non-superusers to attach attachments only to articles they own you can use::

    class AttachmentAdmin(ForeignKeyAutocompleteAdmin):

        ...

        def get_related_filter(self, model, request):
            user = request.user
            if not issubclass(model, Article) or user.is_superuser():
                return super(AttachmentAdmin, self).get_related_filter(
                    model, request
                )
            return Q(owner=user)

Note that this does not protect your application from malicious attempts to
circumvent it (e.g. sending fabricated requests via cURL).
