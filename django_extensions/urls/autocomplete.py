from django.conf.urls.defaults import *

from django_extensions.views.autocomplete import foreignkey_autocomplete

urlpatterns = patterns('',
    url(r'^foreignkey/$', foreignkey_autocomplete, name="foreignkey_autocomplete"),
)
