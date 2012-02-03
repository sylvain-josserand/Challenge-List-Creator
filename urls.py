from django.conf.urls.defaults import *
import settings
from os import getenv 

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('clc.views',
    (r'^$', 'index'),
    (r'^logout$', 'logout'),
    (r'^delete$', 'delete'),
    (r'^add$', 'add'),
    (r'^send$', 'send'),
    (r'^send_password$', 'send_password'),
    (r'^grab$', 'grab'),
    (r'^save$', 'save'),
    (r'^reset_password/(?P<list_name>.*)$', 'reset_password'),
    (r'^(?P<list_name>.*)$', 'display'),
    # Example:
    # (r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
if getenv("DJANGO_MEDIA", False):
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns = patterns('',
                                (r'^%s(?P<path>.*)$' % _media_url,
                                serve,
                                {'document_root': settings.MEDIA_ROOT}))+urlpatterns
    del(_media_url, serve)

