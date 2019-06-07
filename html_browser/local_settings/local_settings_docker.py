import os
from html_browser._os import joinPaths

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
print("file = %s" % __file__)
print("BASE_DIR=%s" % BASE_DIR)
BASE_DIR = BASE_DIR.replace(os.sep, '/')
print("BASE_DIR=%s" % BASE_DIR)

BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '/config/hb.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

STATIC_URL = '/hbmedia/'
STATICFILES_DIRS = ((joinPaths(BASE_DIR, 'media')),)
STATIC_ROOT = joinPaths(BASE_DIR, 'staticfiles')
print('STATIC_ROOT = %s' % STATIC_ROOT)
print("STATICFILES_DIRS=%s" % STATICFILES_DIRS)

LOG_DIR = '/config/log'

THUMBNAIL_CACHE_DIR = '/config/thumb_cache'

ALLOWED_HOSTS = ['userver', 'localhost']
