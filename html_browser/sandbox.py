import os
import sys
sys.path.insert(0, '/srv/www/hb')
os.environ['DJANGO_SETTINGS_MODULE'] = 'html_browser_site.settings'
from django.contrib.auth.models import User, Group  # noqa: E402


user = User.objects.all()[1]
group = Group.objects.all()[1]
# val = group in user.groups
