"""
WSGI config for html_browser project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "html_browser.settings")

application = get_wsgi_application()

import html_browser.monitor
html_browser.monitor.start(interval=1.0)
