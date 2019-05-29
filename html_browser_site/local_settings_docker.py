import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.join('../', __file__))))

with open('/config/local_settings.json') as f:
    configs = json.loads(f.read())

ADMINS = (configs['ADMIN_NAME'], configs['ADMIN_EMAIL'])

DATABASES = configs['DATABASES']

STATIC_URL = configs['STATIC_URL']
STATICFILES_DIRS = tuple(configs['STATICFILES_DIRS'])

LOG_DIR = configs['LOG_DIR']

ALLOWED_HOSTS = configs['ALLOWED_HOSTS']

THUMBNAIL_CACHE_DIR = configs['THUMBNAIL_CACHE_DIR']
