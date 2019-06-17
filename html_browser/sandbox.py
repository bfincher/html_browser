import os
import sys

from django.contrib.auth.models import Group, User  # noqa: E402

sys.path.insert(0, '/srv/www/hb')
os.environ['DJANGO_SETTINGS_MODULE'] = 'html_browser.settings'


user = User.objects.all()[1]
group = Group.objects.all()[1]
# val = group in user.groups
