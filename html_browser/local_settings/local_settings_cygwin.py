import os

from html_browser._os import join_paths

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASE_DIR = BASE_DIR.replace(os.sep, '/')

BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': join_paths(BASE_DIR, 'hb.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

STATICFILES_DIRS = ((join_paths(BASE_DIR, 'media')),)

LOG_DIR = join_paths(BASE_DIR, 'log')

THUMBNAIL_CACHE_DIR = join_paths(BASE_DIR, 'thumb_cache')

ALLOWED_HOSTS = ['userver', 'localhost']

INTERNAL_IPS = ['192.168.1.2', '192.168.1.103']
