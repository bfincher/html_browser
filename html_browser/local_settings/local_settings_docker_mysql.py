import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASE_DIR = BASE_DIR.replace(os.sep, '/')

BASE_DIR_REALPATH = os.path.realpath(BASE_DIR).replace(os.sep, '/')

with open('/config/local_settings.json') as f:
    configs = json.loads(f.read())

_strings_to_replace = {"${BASE_DIR}": BASE_DIR}


def _replace_list(values):
    for i in range(0, len(values)):
        value = values[i]
        if type(value) is list:
            _replace_list(value)
        elif type(value) is dict:
            _replace_dict(value)
        else:
            for key in _strings_to_replace:
                values[i] = value.replace(key, _strings_to_replace[key])


def _replace_dict(_dict):
    for key in _dict:
        value = _dict[key]
        if type(value) is list:
            _replace_list(value)
        elif type(value) is dict:
            _replace_dict(value)
        else:
            for str_to_replace in _strings_to_replace:
                _dict[key] = value.replace(str_to_replace, _strings_to_replace[str_to_replace])


_replace_dict(configs)

ADMINS = (configs['ADMIN_NAME'], configs['ADMIN_EMAIL'])

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASS"],
        "HOST": os.environ["DB_HOST"],
        "PORT": "",
    }
}

STATICFILES_DIRS = tuple(configs['STATICFILES_DIRS'])

LOG_DIR = configs['LOG_DIR']

ALLOWED_HOSTS = configs['ALLOWED_HOSTS']

THUMBNAIL_CACHE_DIR = configs['THUMBNAIL_CACHE_DIR']
