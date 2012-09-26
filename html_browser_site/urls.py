from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from html_browser.models import Folder
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^hb/admin/', include(admin.site.urls)),
    url(r'^hb/', include('html_browser.urls')),
#    url(r"^hb/__media__/(?P<path>.*)$", 
#                "dynamic_media_serve.serve", {"document_root": "/home/bfincher/media"}),
#	url(r"^hb/__media2__/(?P<path>.*)$", 
#                "dynamic_media_serve.serve", {"document_root": "/home/bfincher/media2"})

)


for folder in Folder.objects.all():
	urlpatterns.extend(patterns('', url(r"^hb/__" + folder.name + "__/(?P<path>.*)$", 
                "dynamic_media_serve.serve", {"document_root": folder.localPath})))
	
	
test = ['media', 'media2']

for s in test:
	urlpatterns.extend(patterns('', url(r"^hb/__" + s + "__/(?P<path>.*)$", 
                "dynamic_media_serve.serve", {"document_root": "/home/bfincher/" + s}))),
