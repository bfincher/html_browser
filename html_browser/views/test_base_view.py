from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import Client

import filecmp
import os
import re
from shutil import rmtree
import tempfile
import unittest
import zipfile
from zipfile import ZipFile

from html_browser.models import Folder, UserPermission, GroupPermission, CAN_READ, CAN_WRITE, CAN_DELETE
from html_browser.views.base_view import reverseContentUrl, FolderAndPath


def contextCheck(testCase, context, user=None, folder=None):
    testCase.assertTrue('csrf_token' in context)

    if user:
        self.assertEquals(user, context['user'])


class BaseViewTest(unittest.TestCase):
    def setUp(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        Folder.objects.all().delete()

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

        self.user3 = User()
        self.user3.username = 'user3'
        self.user3Pw = 'test_pw_3'
        self.user3.set_password(self.user3Pw)
        self.user3.save()
        self.user3.save()

        self.users = {self.user1.username: self.user1Pw,
                      self.user2.username: self.user2Pw,
                      self.user3.username: self.user3Pw}

        self.folder1 = Folder()
        self.folder1.name = 'test'
        self.folder1.localPath = 'html_browser/test_dir'
        self.folder1.viewOption = 'P'
        self.folder1.save()

        userPerm = UserPermission()
        userPerm.folder = self.folder1
        userPerm.permission = CAN_DELETE
        userPerm.user = self.user1
        userPerm.save()

        userPerm = UserPermission()
        userPerm.folder = self.folder1
        userPerm.permission = CAN_READ
        userPerm.user = self.user3
        userPerm.save()

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
        # test user1
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

        # test anonymous
        response = self.client.get(reverse('index'))
        self.assertEquals(200, response.status_code)

        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(1, len(context['folders']))
        self.assertEquals(self.folder4, context['folders'][0])
        self.assertEquals('index.html', response.templates[0].name)

        self.logout()

        # test user2
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
        self.assertEquals('/', response.url)


class DownloadViewTest(BaseViewTest):
    def testDownload(self):
        self.login(self.user1)
        url = reverseContentUrl(FolderAndPath(folder=self.folder1, path=''), extraArgs=['file_a.txt'],
                                viewName='download')
        response = self.client.get(url)

        foundAttachment = False
        for item in list(response.items()):
            if item[1] == 'attachment; filename="file_a.txt"':
                foundAttachment = True
                break

        self.assertTrue(foundAttachment)


class DownloadZipViewTest(BaseViewTest):
    def testDownloadZip(self):
        self.login(self.user1)
        response = self.client.get(reverseContentUrl(FolderAndPath(folder=self.folder1, path=''),
                                                     viewName='downloadZip'),
                                   data={'cb-file_a.txt': 'on',
                                         'cb-file_b.txt': 'on',
                                         'cb-dir_a': 'on'})

        self.assertEquals(200, response.status_code)

        attachmentRegex = re.compile(r'attachment; filename="(download_\w+\.zip)"')
        zipFileName = None
        extractPath = "/tmp/extract"

        try:
            for item in list(response.items()):
                match = attachmentRegex.match(item[1])
                if match:
                    zipFileName = match.group(1)
                    break

            self.assertIsNotNone(zipFileName)

            zipFile = ZipFile(os.path.join('/tmp', zipFileName), mode='r')
            entries = zipFile.infolist()

            os.mkdir(extractPath)
            for entry in entries:
                zipFile.extract(entry, extractPath)

            extractedFileA = os.path.join(extractPath, 'file_a.txt')
            extractedFileB = os.path.join(extractPath, 'file_b.txt')
            extractedTestFile = os.path.join(extractPath, 'dir_a/test_file.txt')

            self.assertTrue(os.path.exists(extractedFileA))
            self.assertTrue(os.path.exists(extractedFileB))
            self.assertTrue(os.path.exists(extractedTestFile))

            self.assertTrue(filecmp.cmp('html_browser/test_dir/file_a.txt', extractedFileA))
            self.assertTrue(filecmp.cmp('html_browser/test_dir/file_b.txt', extractedFileB))
            self.assertTrue(filecmp.cmp('html_browser/test_dir/dir_a/test_file.txt', extractedTestFile))
        finally:
            if os.path.exists(extractPath):
                rmtree(extractPath)
            if zipFileName and os.path.exists(zipFileName):
                os.remove(zipFileName)


class UploadViewTest(BaseViewTest):
    def testGet(self):
        self.login(self.user1)
        response = self.client.get(reverseContentUrl(FolderAndPath(folder=self.folder1, path=''),
                                                     viewName='upload'))

        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals('upload.html', response.templates[0].name)

        # test unauthorized user
        self.logout()
        self.login(self.user3)
        response = self.client.get(reverseContentUrl(FolderAndPath(folder=self.folder1, path=''),
                                                     viewName='upload'))

        self.assertEquals(403, response.status_code)

    def testUpload(self):
        self.login(self.user1)

        try:
            with open('html_browser/test_dir/file_a.txt', 'r') as f:
                response = self.client.post(reverseContentUrl(FolderAndPath(folder=self.folder1, path='dir_a'), viewName='upload'),
                                            data={'action': 'uploadFile',
                                                  'upload1': f})

            self.assertEquals(302, response.status_code)

            self.assertTrue(os.path.exists('html_browser/test_dir/dir_a/file_a.txt'))
            self.assertTrue(filecmp.cmp('html_browser/test_dir/dir_a/file_a.txt', 'html_browser/test_dir/dir_a/file_a.txt'))
        finally:
            if os.path.exists('html_browser/test_dir/dir_a/file_a.txt'):
                os.remove('html_browser/test_dir/dir_a/file_a.txt')

    def testUploadNoAuth(self):
        self.login(self.user3)

        try:
            with open('html_browser/test_dir/file_a.txt', 'r') as f:
                response = self.client.post(reverseContentUrl(FolderAndPath(folder=self.folder1, path='dir_a'), viewName='upload'),
                                            data={'action': 'uploadFile',
                                                  'upload1': f})

            self.assertEquals(403, response.status_code)
        finally:
            if os.path.exists('html_browser/test_dir/dir_a/file_a.txt'):
                os.remove('html_browser/test_dir/dir_a/file_a.txt')

    def testUploadZip(self):
        self.login(self.user1)

        zipFileName = tempfile.mktemp(prefix="test_zip", suffix=".zip")
        destFiles = []
        try:
            zipFile = ZipFile(zipFileName, mode='w', compression=zipfile.ZIP_DEFLATED)
            basePath = 'html_browser/test_dir/'

            entries = ['html_browser/test_dir/file_a.txt',
                       'html_browser/test_dir/file_b.txt']

            for entry in entries:
                arcName = entry.replace(basePath, '')
                zipFile.write(entry, arcName, compress_type=zipfile.ZIP_DEFLATED)

            zipFile.close()

            with open(zipFileName, 'rb') as f:
                response = self.client.post(reverseContentUrl(FolderAndPath(folder=self.folder1, path='dir_a'), viewName='upload'),
                                            data={'action': 'uploadZip',
                                                  'zipupload1': f})

                self.assertEquals(302, response.status_code)
                destFiles = ['html_browser/test_dir/dir_a/file_a.txt',
                             'html_browser/test_dir/dir_a/file_b.txt']
                for destFile in destFiles:
                    self.assertTrue(os.path.exists(destFile))
        finally:
            if os.path.exists(zipFileName):
                os.remove(zipFileName)
            for destFile in destFiles:
                if os.path.exists(destFile):
                    os.remove(destFile)
