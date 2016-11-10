from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from html_browser.models import Folder
from .settings import URL_PREFIX
#import dynamic_media_serve
admin.autodiscover()

urlpatterns = [ 
	url(URL_PREFIX + r'admin/', include(admin.site.urls)),
    url(URL_PREFIX, include('html_browser.urls')),
    #url(URL_PREFIX + r'__media__/(?P<path>.*)$',  
                #"dynamic_media_serve.serve", {"document_root": "/srv/www/hb/media"}),
    ]


#for folder in Folder.objects.all():
#	urlpatterns.append(url(URL_PREFIX + r"__" + folder.name + r"__/(?P<path>.*)$", 
#                dynamic_media_serve.serve, {"document_root": folder.localPath}))
	
