import os
import sys
 
path = '/srv/www'
if path not in sys.path:
    sys.path.insert(0, '/srv/www/hbtest')
 
os.environ['DJANGO_SETTINGS_MODULE'] = 'html_browser_site.settings'
 
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
