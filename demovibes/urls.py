from django.conf.urls.defaults import *
from demovibes.webview.views import about_pages
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'django.views.generic.simple.redirect_to', {'url': '/demovibes/'}),
    #(r'^$', 'django.views.generic.simple.redirect_to', {'url': '/static/biebervibes/'}),  # April 1st 2015
    (r'^accounts/profile/$', 'django.views.generic.simple.redirect_to', {'url': '/demovibes/'}),
    (r'^accounts/logout/$', 'webview.views.log_out'),
    (r'^demovibes/', include('demovibes.webview.urls')),
    (r'^openid/', include('demovibes.openid_provider.urls')),
    (r'^search/', include('demovibes.search.urls')),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('demovibes.registration.urls')),
    (r'^account/', include('django_authopenid.urls')),
    (r'^forum/', include('forum.urls')),

    (r'^about/(\w+)/$', about_pages),
)
if settings.DEBUG:
    #Only use this under development!! Only for serving static files with dev server!
    urlpatterns += patterns('', (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}))

