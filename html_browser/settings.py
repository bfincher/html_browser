#  Django settings for html_browser project.
import os
import json
import environ  # type: ignore

from html_browser._os import join_paths

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BASE_DIR = BASE_DIR.replace(os.sep, '/')
BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')
URL_PREFIX = ''
INTERNAL_IPS = []

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

env = environ.Env(
    DEBUG=(bool, False),
    THUMBNAIL_DEBUG=(bool, False),
    ADMINS=(tuple, ('Your Name', 'your_email@example.com')),
    URL_PREFIX=(str, r''),
    LOGIN_URL=(str, '/'),
    TIME_ZONE=(str, 'America/Chicago'),
    LOG_DIR=(str, join_paths(BASE_DIR, 'log')),
    ALLOWED_HOSTS=(list, ['localhost']),
    INTERNAL_IPS=(list, ['127.0.0.1']),
    THUMBNAIL_CACHE_DIR=(str, join_paths(BASE_DIR, 'thumb_cache')),
    DB_ENGINE=(str, None),
    DB_NAME=(str, None),
    DB_OPTIONS=(dict, {}),
    DB_USER=(str, ''),
    DB_PASS=(str, ''),
    DB_HOST=(str, ''),
    DB_PORT=(str, ''),
    STATICFILES_DIRS=(tuple, ()),
    EXTRA_CONFIG_DIR=(str, BASE_DIR)
)
environ.Env.read_env(join_paths(BASE_DIR, '.env'))

ALLOWED_HOSTS = env('ALLOWED_HOSTS')
DEBUG = env('DEBUG')
THUMBNAIL_DEBUG = env('THUMBNAIL_DEBUG')
INTERNAL_IPS = env('INTERNAL_IPS')
THUMBNAIL_CACHE_DIR = env('THUMBNAIL_CACHE_DIR')
EXTRA_CONFIG_DIR = env('EXTRA_CONFIG_DIR')


def buildLoginUrl():
    if URL_PREFIX and not LOGIN_URL.startswith("URL_PREFIX"):
        loginUrl = URL_PREFIX + LOGIN_URL
        loginUrl = loginUrl.replace("//", "/")
        return loginUrl
    return LOGIN_URL


URL_PREFIX = env('URL_PREFIX')
LOGIN_URL = env('LOGIN_URL')
LOGIN_URL = buildLoginUrl()

DOWNLOADVIEW_BACKEND = 'django_downloadview.apache.XSendfileMiddleware'


def buildStaticFilesDirs():
    baseDirPrefix = '__BASE_DIR__'
    tmpList = env('STATICFILES_DIRS')
    toReturn = []

    for entry in tmpList:
        if entry.startswith(baseDirPrefix):
            entry = join_paths(BASE_DIR, entry[len(baseDirPrefix):])
        toReturn.append(entry)

    return tuple(toReturn)


STATICFILES_DIRS = buildStaticFilesDirs()

THUMBNAIL_FAST_URL = True
THUMBNAIL_STORAGE = 'html_browser.utils.ThumbnailStorage'

MANAGERS = env('ADMINS')

dboptions = {}
if env.str('DB_INIT_COMMAND', None):
    dboptions['init_command'] = env('DB_INIT_COMMAND')

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE'),
        'NAME': env('DB_NAME'),
        'OPTIONS': dboptions,
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASS'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT')
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = env('TIME_ZONE')

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

STATIC_URL = "/hbmedia/"
STATIC_ROOT = 'hbmedia'
# STATIC_ROOT = join_paths(BASE_DIR, 'media')

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'm9pu5&amp;-q3&amp;@x!d9ldr9vc1tb7qgj-i*ygui%snx0azfew%r39a'

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    # 'django_downloadview.SmartDownloadMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'html_browser.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'html_browser.wsgi.application'

JS_REVERSE_JS_MINIFY = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [join_paths(BASE_DIR, 'html_browser/templates'),
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
            'debug': True,
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
    'debug_toolbar',
    'django_js_reverse',
    'django_downloadview',
    'sorl.thumbnail',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

CRISPY_TEMPLATE_PACK = 'bootstrap4'

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

LOG_DIR = env('LOG_DIR')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

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
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join_paths(LOG_DIR, 'hb.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'standard',
        },
        'request_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join_paths(LOG_DIR, 'request.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'standard',

        },
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
        'sorl.thumbnail': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}


def readExtraSettings():
    extraConfigDir = env('EXTRA_CONFIG_DIR')
    configFile = join_paths(extraConfigDir, 'local_settings.json')
    if os.path.exists(configFile):
        with open(configFile, encoding='utf8') as f:
            data = json.load(f)
        if 'ALLOWED_HOSTS' in data:
            ALLOWED_HOSTS.extend(data['ALLOWED_HOSTS'])

        if 'URL_PREFIX' in data:
            global URL_PREFIX  # pylint: disable=global-statement
            URL_PREFIX = data['URL_PREFIX']

            global LOGIN_URL # pylint: disable=global-statement
            LOGIN_URL = buildLoginUrl()

        if 'INTERNAL_IPS' in data:
            INTERNAL_IPS.extend(data['INTERNAL_IPS'])

        if 'DEBUG' in data:
            global DEBUG # pylint: disable=global-statement
            DEBUG = bool(data['DEBUG'])


readExtraSettings()
