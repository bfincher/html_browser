import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.join('../', __file__))))
BASE_DIR = BASE_DIR.replace(os.sep, '/')

BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'NAME': 'hb',                      # Or path to database file if using sqlite3.
        'USER': 'hb',                      # Not used with sqlite3.
        'PASSWORD': 'hb',                  # Not used with sqlite3.
        'HOST': 'DB_HOST',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

STATIC_URL = None
STATICFILES_DIRS = ()

LOG_DIR = '/var/log/hb'

THUMBNAIL_CACHE_DIR = os.path.join(BASE_DIR, 'thumb_cache')
