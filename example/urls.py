from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()
from example.blog.views import test_form

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^autocomplete/', include("django_extensions.urls.autocomplete")),
    url(r'^test_form/', test_form),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT}),
        url(r'^admin_media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.ADMIN_MEDIA_ROOT}),
    )
