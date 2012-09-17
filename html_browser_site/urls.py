from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
#	url(r'^hb/admin/', include(admin.site.urls)),
    url(r'^hb/', include('html_browser.urls')),
)
