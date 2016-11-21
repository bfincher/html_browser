# Django settings for html_browser_site project.
import os
import platform

URL_PREFIX = r''
SENDFILE_BACKEND = 'sendfile.backends.xsendfile'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(os.path.join('../', __file__))))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES=None

DATABASES_CYGWIN = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '/home/n86538/tmp/html_browser_python/hb.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

DATABASES_LINUX = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'hb',                      # Or path to database file if using sqlite3.
        'USER': 'hb',                      # Not used with sqlite3.
        'PASSWORD': 'hb',                  # Not used with sqlite3.
        'HOST': 'DB_HOST',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

if platform.system().startswith("CYG"):
    DATABASES=DATABASES_CYGWIN
    DATABASES['default']['NAME'] = os.path.dirname(os.path.abspath(__file__)) + "/../hb.db"
else:
    DATABASES=DATABASES_LINUX

THUMBNAIL_DIR = '/srv/www/hb/media/thumbs'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = None

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

if platform.system().startswith("CYG"):
    # URL prefix for static files.
    # Example: "http://media.lawrence.com/static/"
    STATIC_URL = '/hbmedia/'

    # Additional locations of static files
    STATICFILES_DIRS = (
        '/home/n86538/tmp/html_browser_python/media',
        # Put strings here, like "/home/html/static" or "C:/www/django/static".
        # Always use forward slashes, even on Windows.
        # Don't forget to use absolute paths, not relative paths.
)
else:
    STATIC_URL = None
    STATICFILES_DIRS = ()


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'm9pu5&amp;-q3&amp;@x!d9ldr9vc1tb7qgj-i*ygui%snx0azfew%r39a'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware'
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'html_browser_site.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'html_browser_site.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'html_browser/templates'),
                 os.path.join(BASE_DIR, 'html_browser_site/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'html_browser.context_processors.media',
                'html_browser.context_processors.images',
            ],
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'html_browser',
    'django.contrib.admin',
    'crispy_forms',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

CRISPY_TEMPLATE_PACK='bootstrap3'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level' : 'DEBUG',
	    'class' : 'logging.handlers.RotatingFileHandler',
	    'filename' : '/var/log/hb/hb.log',
	    'maxBytes' : 1024*1024*10, # 10 MB
	    'backupCount' : 5,
	    'formatter' : 'standard',
	},
	'request_handler' : {
	    'level' : 'DEBUG',
	    'class' : 'logging.handlers.RotatingFileHandler',
	    'filename' : '/var/log/hb/request.log',
	    'maxBytes' : 1024*1024*10, # 10 MB
	    'backupCount' : 5,
	    'formatter' : 'standard',

	},
#        'mail_admins': {
#            'level': 'ERROR',
#            'filters': ['require_debug_false'],
#            'class': 'django.utils.log.AdminEmailHandler'
#        }
    },
    'loggers': {
        'html_browser': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
