from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django_js_reverse.views import urls_js
from .settings import URL_PREFIX
admin.autodiscover()

urlpatterns = [
    url(URL_PREFIX + r'jsreverse/$', urls_js, name='js_reverse'),
#    url(URL_PREFIX + r'admin/', include(admin.site.urls)),
    url(URL_PREFIX, include('html_browser.urls')),
]
