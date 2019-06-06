import os
import sys
import site

site.addsitedir('/var/www/.virtualenvs/html_browser/lib/python3.5/site-packages')

path = '/srv/www/hb'
if path not in sys.path:
    sys.path.insert(0, '/srv/www/hb')

os.environ['DJANGO_SETTINGS_MODULE'] = 'html_browser.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import html_browser.monitor
html_browser.monitor.start(interval=1.0)
