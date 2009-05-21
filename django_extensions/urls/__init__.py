from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^autocomplete/', include('django_extensions.urls.autocomplete')),
)
