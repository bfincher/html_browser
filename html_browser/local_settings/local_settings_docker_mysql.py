import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASE_DIR = BASE_DIR.replace(os.sep, '/')

BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')

with open('/config/local_settings.json') as f:
    configs = json.loads(f.read())

_stringsToReplace = {"${BASE_DIR}": BASE_DIR}


def _replaceList(values):
    for i in range(0, len(values)):
        value = values[i]
        if type(value) is list:
            _replaceList(value)
        elif type(value) is dict:
            _replaceDict(value)
        else:
            for key in _stringsToReplace:
                values[i] = value.replace(key, _stringsToReplace[key])


def _replaceDict(_dict):
    for key in _dict:
        value = _dict[key]
        if type(value) is list:
            _replaceList(value)
        elif type(value) is dict:
            _replaceDict(value)
        else:
            for strToReplace in _stringsToReplace:
                _dict[key] = value.replace(strToReplace, _stringsToReplace[strToReplace])


_replaceDict(configs)

ADMINS = (configs['ADMIN_NAME'], configs['ADMIN_EMAIL'])

DATABASES = configs['DATABASES']
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": "localhost",
        "PORT": "",
    }
}

STATICFILES_DIRS = tuple(configs['STATICFILES_DIRS'])

LOG_DIR = configs['LOG_DIR']

ALLOWED_HOSTS = configs['ALLOWED_HOSTS']

THUMBNAIL_CACHE_DIR = configs['THUMBNAIL_CACHE_DIR']
