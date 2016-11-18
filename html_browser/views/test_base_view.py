from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import Client

import unittest

from  html_browser.models import Folder, UserPermission, GroupPermission, CAN_READ, CAN_WRITE, CAN_DELETE

def contextCheck(testCase, context, user=None, folder=None):
    testCase.assertTrue('csrf_token' in context)
    testCase.assertTrue('const' in context)

    if user:
        self.assertEquals(user, context['user'])
    

class BaseViewTest(unittest.TestCase):
    def setUp(self):
         self.user1 = User()
         self.user1.username = 'user1'
         self.user1Pw = 'test_pw_1'
         self.user1.set_password(self.user1Pw)
         self.user1.save()

         group1 = Group()
         group1.name = 'test group1'
         group1.save()

         self.user2 = User()
         self.user2.username = 'user2'
         self.user2Pw = 'test_pw_2'
         self.user2.set_password(self.user2Pw)
         self.user2.save()
         self.user2.groups.add(group1)
         self.user2.save()

         self.users = {self.user1.username: self.user1Pw,
                       self.user2.username: self.user2Pw}

         self.folder1 = Folder()
         self.folder1.name = 'test'
         self.folder1.localPath = 'html_browser/test_dir'
         self.folder1.viewOption = 'P'
         self.folder1.save()

         userPerm1 = UserPermission()
         userPerm1.folder = self.folder1
         userPerm1.permission = CAN_DELETE
         userPerm1.user = self.user1
         userPerm1.save()

         self.folder2 = Folder()
         self.folder2.name = 'test2'
         self.folder2.localPath = 'test2'
         self.folder2.viewOption = 'P'
         self.folder2.save()

         self.folder3 = Folder()
         self.folder3.name = 'test3'
         self.folder3.localPath = 'test3'
         self.folder3.viewOption = 'E'
         self.folder3.save()

         self.folder4 = Folder()
         self.folder4.name = 'test4'
         self.folder4.localPath = 'test4'
         self.folder4.viewOption = 'A'
         self.folder4.save()

         groupPerm1 = GroupPermission()
         groupPerm1.folder = self.folder2
         groupPerm1.permission = CAN_DELETE
         groupPerm1.group = group1
         groupPerm1.save()

         self.client = Client()

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        Folder.objects.all().delete()

    def login(self, user):
        return self.client.post(reverse('login'), data={'userName': user.username, 'password': self.users[user.username]})

    def logout(self):
        return self.client.get(reverse('logout'))


class IndexViewTest(BaseViewTest):
    def test(self):
        ### test user1
        self.login(self.user1)
        response = self.client.get(reverse('index'))
        self.assertEquals(200, response.status_code)

        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(3, len(context['folders']))
        self.assertEquals(self.folder1, context['folders'][0])
        self.assertEquals(self.folder3, context['folders'][1])
        self.assertEquals(self.folder4, context['folders'][2])
        self.assertEquals('index.html', response.templates[0].name)

        self.logout()

        ### test anonymous
        response = self.client.get(reverse('index'))
        self.assertEquals(200, response.status_code)

        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(1, len(context['folders']))
        self.assertEquals(self.folder4, context['folders'][0])
        self.assertEquals('index.html', response.templates[0].name)

        self.logout()

        ## test user2
        self.login(self.user2)
        self.client.force_login(self.user2)
        response = self.client.get(reverse('index'))
        self.assertEquals(200, response.status_code)

        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(3, len(context['folders']))
        self.assertEquals(self.folder2, context['folders'][0])
        self.assertEquals(self.folder3, context['folders'][1])
        self.assertEquals(self.folder4, context['folders'][2])
        self.assertEquals('index.html', response.templates[0].name)


class LoginViewTest(BaseViewTest):
    def testLogin(self):
        response = self.client.post(reverse('login'), data={'userName': self.user1.username, 'password': self.user1Pw})
        self.assertEquals(302, response.status_code)
        self.assertEquals('/', response.url)


class LogoutViewTest(BaseViewTest):
    def testLogout(self):
        self.login(self.user1)
        response = self.logout()
        self.assertEquals(302, response.status_code)
        self.assertEquals('/hb/', response.url)

class DownloadViewTest(BaseViewTest):
    def testDownload(self):
        self.login(self.user1)
        response = self.client.get(reverse('download'), 
            data={'currentFolder': self.folder1.name,
                  'currentPath': '/',
                  'fileName': 'file_a.txt'})

        foundAttachment = False
        for item in list(response.items()):
            if item[1] == 'html_browser/test_dir//file_a.txt':
                foundAttachment = True
                break
        
        self.assertTrue(foundAttachment)
