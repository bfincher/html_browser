from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client

import unittest

from  html_browser.models import Folder


class IndexViewTest(unittest.TestCase):
    def setUp(self):
         self.user1 = User()
         self.user1.username = 'unit test user1'
         self.user1.save()

         self.folder = Folder()
         self.folder.name = 'test'
         self.folder.localPath = 'html_browser/test_dir'
         self.folder.viewOption = 'E'
         self.folder.save()

         self.client = Client()

    def testIndexView(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('index'))
        self.assertEquals(200, response.status_code)

        context = response.context[0]
        print(context)
        self.assertEquals(self.user1, context['user'])
        self.assertTrue('csrf_token' in context)
        self.assertTrue('const' in context)
        self.assertEquals(1, len(context['folders']))
        self.assertEquals(self.folder, context['folders'][0])
         

