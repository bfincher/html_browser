import os
from html_browser._os import joinPaths

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.join('../', __file__))))
BASE_DIR = BASE_DIR.replace(os.sep, '/')

BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': joinPaths(BASE_DIR, 'hb.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

STATIC_URL = '/hbmedia/'
STATICFILES_DIRS = ((joinPaths(BASE_DIR, 'media')),)

LOG_DIR = joinPaths(BASE_DIR, 'log')

THUMBNAIL_CACHE_DIR = joinPaths(BASE_DIR, 'thumb_cache')

ALLOWED_HOSTS = ['userver', 'localhost']
