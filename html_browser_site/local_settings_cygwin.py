import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.join('../', __file__))))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_DIR, 'hb.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

STATIC_URL = '/hbmedia/'
STATICFILES_DIRS = ((os.path.join(BASE_DIR, 'media')),)

LOG_DIR = '/var/log/hb'

THUMBNAIL_CACHE_DIR = os.path.join(BASE_DIR, 'thumb_cache')

ALLOWED_HOSTS = ['userver', 'localhost']
