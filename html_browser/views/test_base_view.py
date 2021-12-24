import filecmp
import os
import re
import tempfile
import unittest
from shutil import rmtree
# import zipfile
from zipfile import ZipFile

from django.contrib.auth.models import Group, User
from django.test import Client
from django.urls import reverse

from html_browser._os import join_paths
from html_browser.models import (CAN_DELETE, CAN_READ, Folder, GroupPermission,
                                 UserPermission)
from html_browser.views.base_view import (FolderAndPath,
                                          get_index_into_current_dir,
                                          reverse_content_url)


def context_check(test_case, context, user=None, folder=None):
    test_case.assertTrue('csrf_token' in context)

    if user:
        test_case.assertEqual(user, context['user'])


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

        self.group1 = Group()
        self.group1.name = 'test_group1'
        self.group1.save()

        self.user2 = User()
        self.user2.username = 'user2'
        self.user2Pw = 'test_pw_2'
        self.user2.set_password(self.user2Pw)
        self.user2.save()
        self.user2.groups.add(self.group1)
        self.user2.save()

        self.user3 = User()
        self.user3.username = 'user3'
        self.user3Pw = 'test_pw_3'
        self.user3.set_password(self.user3Pw)
        self.user3.save()

        self.users = {self.user1.username: self.user1Pw,
                      self.user2.username: self.user2Pw,
                      self.user3.username: self.user3Pw}

        self.folder1 = Folder()
        self.folder1.name = 'test'
        self.folder1.local_path = 'media'
        self.folder1.view_option = 'P'
        self.folder1.save()

        user_perm = UserPermission()
        user_perm.folder = self.folder1
        user_perm.permission = CAN_DELETE
        user_perm.user = self.user1
        user_perm.save()

        user_perm = UserPermission()
        user_perm.folder = self.folder1
        user_perm.permission = CAN_READ
        user_perm.user = self.user3
        user_perm.save()

        self.folder2 = Folder()
        self.folder2.name = 'test2'
        self.folder2.local_path = 'test2'
        self.folder2.view_option = 'P'
        self.folder2.save()

        self.folder3 = Folder()
        self.folder3.name = 'test3'
        self.folder3.local_path = 'test3'
        self.folder3.view_option = 'E'
        self.folder3.save()

        self.folder4 = Folder()
        self.folder4.name = 'test4'
        self.folder4.local_path = 'test4'
        self.folder4.view_option = 'A'
        self.folder4.save()

        self.folders = [self.folder1, self.folder2, self.folder3, self.folder4]

        group_perm_1 = GroupPermission()
        group_perm_1.folder = self.folder2
        group_perm_1.permission = CAN_DELETE
        group_perm_1.group = self.group1
        group_perm_1.save()

        self.client = Client()

    def tear_down(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        Folder.objects.all().delete()

    def login(self, user, password=None, follow=False):
        password = password or self.users[user.username]
        return self.client.post(reverse('login'), data={'user_name': user.username, 'password': password}, follow=follow)

    def logout(self):
        return self.client.get(reverse('logout'))

    def assert_message_count(self, response, expect_num):
        """
        Asserts that exactly the given number of messages have been sent.
        """

        actual_num = len(response.context['messages'])
        if actual_num != expect_num:
            self.fail('Message count was %d, expected %d' %
                      (actual_num, expect_num))

    def assert_message_contains(self, response, text, level=None):
        """
        Asserts that there is exactly one message containing the given text.
        """

        messages = response.context['messages']

        matches = [m for m in messages if text in m.message]

        if len(matches) == 1:
            msg = matches[0]
            if level is not None and msg.level != level:
                self.fail('There was one matching message but with different'
                          'level: %s != %s' % (msg.level, level))

                return

        elif len(matches) == 0:
            messages_str = ", ".join('"%s"' % m for m in messages)
            self.fail('No message contained text "%s", messages were: %s' %
                      (text, messages_str))
        else:
            self.fail('Multiple messages contained text "%s": %s' %
                      (text, ", ".join(('"%s"' % m) for m in matches)))

    def assert_message_not_contains(self, response, text):
        """ Assert that no message contains the given text. """

        messages = response.context['messages']

        matches = [m for m in messages if text in m.message]

        if len(matches) > 0:
            self.fail('Message(s) contained text "%s": %s' %
                      (text, ", ".join(('"%s"' % m) for m in matches)))


class IndexViewTest(BaseViewTest):
    def test(self):
        # test user1
        self.login(self.user1)
        response = self.client.get(reverse('index'))
        self.assertEqual(200, response.status_code)

        context = response.context[0]
        context_check(self, context)
        self.assertEqual(3, len(context['folders']))
        self.assertEqual(self.folder1, context['folders'][0])
        self.assertEqual(self.folder3, context['folders'][1])
        self.assertEqual(self.folder4, context['folders'][2])
        self.assertEqual('index.html', response.templates[0].name)

        self.logout()

        # test anonymous
        response = self.client.get(reverse('index'))
        self.assertEqual(200, response.status_code)

        context = response.context[0]
        context_check(self, context)
        self.assertEqual(1, len(context['folders']))
        self.assertEqual(self.folder4, context['folders'][0])
        self.assertEqual('index.html', response.templates[0].name)

        self.logout()

        # test user2
        self.login(self.user2)
        self.client.force_login(self.user2)
        response = self.client.get(reverse('index'))
        self.assertEqual(200, response.status_code)

        context = response.context[0]
        context_check(self, context)
        self.assertEqual(3, len(context['folders']))
        self.assertEqual(self.folder2, context['folders'][0])
        self.assertEqual(self.folder3, context['folders'][1])
        self.assertEqual(self.folder4, context['folders'][2])
        self.assertEqual('index.html', response.templates[0].name)


class LoginViewTest(BaseViewTest):
    def testLogin(self):
        response = self.client.post(reverse('login'), data={'user_name': self.user1.username, 'password': self.user1Pw})
        self.assertEqual(302, response.status_code)
        self.assertEqual('/', response.url)


class LogoutViewTest(BaseViewTest):
    def testLogout(self):
        self.login(self.user1)
        response = self.logout()
        self.assertEqual(302, response.status_code)
        self.assertEqual('/', response.url)


class DownloadViewTest(BaseViewTest):
    def testDownload(self):
        self.login(self.user1)
        url = reverse_content_url(FolderAndPath(folder=self.folder1, path=''), extra_path='add_user.js',
                                  view_name='download')
        response = self.client.get(url)

        found_attachment = False
        for item in list(response.items()):
            if item[1] == 'attachment; filename="add_user.js"':
                found_attachment = True
                break

        self.assertTrue(found_attachment)


class DownloadZipViewTest(BaseViewTest):
    def testDownloadZip(self):
        self.login(self.user1)
        response = self.client.get(reverse_content_url(FolderAndPath(folder=self.folder1, path=''),
                                                       view_name='downloadZip'),
                                   data={'cb-add_user.js': 'on',
                                         'cb-base.js': 'on',
                                         'cb-images': 'on'})

        self.assertEqual(200, response.status_code)

        attachment_regex = re.compile(r'attachment; filename="(download_\w+\.zip)"')
        zip_file_name = None
        tmp_dir = tempfile.gettempdir()

        extract_path = join_paths(tmp_dir, 'extract')
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        try:
            for item in list(response.items()):
                match = attachment_regex.match(item[1])
                if match:
                    zip_file_name = match.group(1)
                    break

            self.assertIsNotNone(zip_file_name)

            zip_file = ZipFile(join_paths(tmp_dir, zip_file_name), mode='r')
            entries = zip_file.infolist()

            os.makedirs(extract_path, exist_ok=True)
            for entry in entries:
                zip_file.extract(entry, extract_path)

            extracted_file_a = join_paths(extract_path, 'add_user.js')
            extracted_file_b = join_paths(extract_path, 'base.js')
            extracted_test_file = join_paths(extract_path, 'images/Add-Folder-icon.png')

            self.assertTrue(os.path.exists(extracted_file_a))
            self.assertTrue(os.path.exists(extracted_file_b))
            self.assertTrue(os.path.exists(extracted_test_file))

            self.assertTrue(filecmp.cmp('media/add_user.js', extracted_file_a))
            self.assertTrue(filecmp.cmp('media/base.js', extracted_file_b))
            self.assertTrue(filecmp.cmp('media/images/Add-Folder-icon.png', extracted_test_file))
        finally:
            if os.path.exists(extract_path):
                rmtree(extract_path)
            if zip_file_name and os.path.exists(zip_file_name):
                os.remove(zip_file_name)


class UploadViewTest(BaseViewTest):
    def testGet(self):
        self.login(self.user1)
        response = self.client.get(reverse_content_url(FolderAndPath(folder=self.folder1, path=''),
                                                       view_name='upload'))

        self.assertEqual(200, response.status_code)
        context = response.context[0]
        context_check(self, context)
        self.assertEqual('upload.html', response.templates[0].name)

        # test unauthorized user
        self.logout()
        self.login(self.user3)
        response = self.client.get(reverse_content_url(FolderAndPath(folder=self.folder1, path=''),
                                                       view_name='upload'))

        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/upload/test/', response.url)
    '''
    def testUpload(self):
        self.login(self.user1)

        try:
            with open('media/base.js', 'r') as f:
                response = self.client.post(reverse_content_url(FolderAndPath(folder=self.folder1, path='images'), view_name='upload'),
                                            data={'action': 'uploadFile',
                                                  'upload1': f})

            self.assertEqual(302, response.status_code)

            self.assertTrue(os.path.exists('media/base.js'))
            self.assertTrue(filecmp.cmp('media/base.js', 'media/images/base.js'))
        finally:
            if os.path.exists('media/images/base.js'):
                os.remove('media/images/base.js')

    def testUploadNoAuth(self):
        self.login(self.user3)

        try:
            with open('media/base.js', 'r') as f:
                response = self.client.post(reverse_content_url(FolderAndPath(folder=self.folder1, path='dir_a'), view_name='upload'),
                                            data={'action': 'uploadFile',
                                                  'upload1': f})

            self.assertEqual(302, response.status_code)
            self.assertEqual('/?next=/upload/test/dir_a/', response.url)
        finally:
            if os.path.exists('media/images/base.js'):
                os.remove('media/images/base.js')

    def testUploadZip(self):
        self.login(self.user1)

        zipFileName = tempfile.mktemp(prefix="test_zip", suffix=".zip")
        destFiles = []
        try:
            zipFile = ZipFile(zipFileName, mode='w', compression=zipfile.ZIP_DEFLATED)
            basePath = 'media'

            entries = ['media/base.js',
                       'media/add_user.js']

            for entry in entries:
                arcName = entry.replace(basePath, '')
                zipFile.write(entry, arcName, compress_type=zipfile.ZIP_DEFLATED)

            zipFile.close()

            with open(zipFileName, 'rb') as f:
                response = self.client.post(reverse_content_url(FolderAndPath(folder=self.folder1, path='images'),
                                                              view_name='upload'),
                                            data={'action': 'uploadZip',
                                                  'zipupload1': f})

                self.assertEqual(302, response.status_code)
                destFiles = ['media/images/base.js',
                             'media/images/add_user.js']
                for destFile in destFiles:
                    self.assertTrue(os.path.exists(destFile))
        finally:
            if os.path.exists(zipFileName):
                os.remove(zipFileName)
            for destFile in destFiles:
                if os.path.exists(destFile):
                    os.remove(destFile)
    '''

    def testImageView(self):
        self.login(self.user1)
        response = self.client.get(reverse_content_url(FolderAndPath(folder=self.folder1, path='images'),
                                                       view_name='imageView', extra_path='folder-blue-icon.png'))

        context = response.context[0]
        context_check(self, context)

        self.assertEqual('/content/test/images/', context['parent_dir_link'])
        self.assertEqual('/imageView/test/images/folder-blue-icon-128.png/', context['prev_link'])
        self.assertEqual('/imageView/test/images/folder-blue-parent-icon.png/', context['next_link'])
        self.assertEqual('/download/test/images/folder-blue-icon.png/', context['image_url'])
        self.assertEqual('folder-blue-icon.png', context['file_name'])
        self.assertTrue(context['user_can_delete'])
        self.assertEqual('image_view.html', response.templates[0].name)

        # test unauthorized user
        self.logout()
        self.login(self.user2)
        response = self.client.get(reverse_content_url(FolderAndPath(folder=self.folder1, path='images'),
                                                       view_name='imageView', extra_path='folder-blue-icon.png'))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/imageView/test/images/folder-blue-icon.png/', response.url)


class TestGetIndexIntoCurrentDir(BaseViewTest):

    class TestRequest():
        def __init__(self):
            self.session = {'show_hidden': False}

    def test(self):
        request = self.TestRequest()
        folder_and_path = FolderAndPath(folder=self.folder1, path='images')

        result = get_index_into_current_dir(request, folder_and_path, 'Add-Folder-icon.png')
        self.assertEqual(0, result['index'])
        self.assertEqual(20, len(result['current_dir_entries']))

        expected_files = ['Add-Folder-icon.png', 'Copy-icon.png', 'Document-icon.png']

        for i in range(len(expected_files)):
            self.assertFalse(result['current_dir_entries'][i].is_dir)
            self.assertFalse(result['current_dir_entries'][i].has_thumbnail)
            self.assertEqual(expected_files[i], result['current_dir_entries'][i].name)
            self.assertEqual(expected_files[i], result['current_dir_entries'][i].name_url)
