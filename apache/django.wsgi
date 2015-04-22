import os
import sys
 
path = '/srv/www/hb'
if path not in sys.path:
    sys.path.insert(0, '/srv/www/hb')
 
os.environ['DJANGO_SETTINGS_MODULE'] = 'html_browser_site.settings'
 
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import html_browser_site.monitor
html_browser_site.monitor.start(interval=1.0)
