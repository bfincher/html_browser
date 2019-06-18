import logging

from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.urls import reverse

from html_browser.models import Folder, Group
from html_browser.views.test_base_view import BaseViewTest, contextCheck

logger = logging.getLogger('html_browser.testAdminViews')


class BaseAdminTest(BaseViewTest):
    def setUp(self):
        super().setUp()

        self.user4 = User()
        self.user4.username = 'user4'
        self.user4Pw = 'test_pw_4'
        self.user4.set_password(self.user4Pw)
        self.user4.is_staff = True
        self.user4.save()

        self.users[self.user4.username] = self.user4Pw


class AdminViewTest(BaseAdminTest):
    def testAdminView(self):
        self.login(self.user4)
        response = self.client.get(reverse('admin'))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual('admin/admin.html', response.templates[0].name)

        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('admin'))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/hbAdmin/', response.url)


class FolderTest(BaseAdminTest):
    def testFolderAdminView(self):
        self.login(self.user4)
        response = self.client.get(reverse('folderAdmin'))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual('admin/folder_admin.html', response.templates[0].name)

        self.assertEqual(len(self.folders), len(context['folders']))
        self.assertEqual(self.folder1, context['folders'][0])
        self.assertEqual(self.folder2, context['folders'][1])
        self.assertEqual(self.folder3, context['folders'][2])
        self.assertEqual(self.folder4, context['folders'][3])

        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('folderAdmin'))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/folderAdmin/', response.url)

    def testDeleteFolder(self):
        self.login(self.user4)
        args = [self.folder2.name]
        response = self.client.post(reverse('deleteFolder', args=args))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/folderAdmin/', response.url)
        self.assertFalse(get_object_or_None(Folder, name=self.folder2.name))

        self.logout()
        self.login(self.user1)
        args = [self.folder3.name]
        response = self.client.post(reverse('deleteFolder', args=args))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/deleteFolder/%s' % self.folder3.name, response.url)
        self.assertTrue(get_object_or_None(Folder, name=self.folder3.name))

    def testEditFolder(self):
        self.login(self.user4)
        data = {
            'user_perm-TOTAL_FORMS': '0',
            'user_perm-INITIAL_FORMS': '0',
            'user_perm-MAX_NUM_FORMS': '1000',
            'group_perm-TOTAL_FORMS': '0',
            'group_perm-INITIAL_FORMS': '0',
            'group_perm-MAX_NUM_FORMS': '1000',
        }
        response = self.client.get(reverse('editFolder', args=[self.folder1.name]), data)
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual(self.user4.username, context['user'].username)
        self.assertEqual(self.folder1.name, context['folder'].name)
        self.assertEqual("admin/add_edit_folder.html", response.templates[0].name)

        data['name'] = self.folder1.name
        data['localPath'] = '/data/newPath'
        data['viewOption'] = 'E'
        response = self.client.post(reverse('editFolder', args=[self.folder1.name]), data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/folderAdmin/', response.url)

        newFolder1 = Folder.objects.get(pk=self.folder1.pk)
        self.assertEqual(self.folder1.name, newFolder1.name)
        self.assertEqual('/data/newPath', newFolder1.localPath)

    def testAddFolder(self):
        self.login(self.user4)
        data = {
            'user_perm-TOTAL_FORMS': '0',
            'user_perm-INITIAL_FORMS': '0',
            'user_perm-MAX_NUM_FORMS': '1000',
            'group_perm-TOTAL_FORMS': '0',
            'group_perm-INITIAL_FORMS': '0',
            'group_perm-MAX_NUM_FORMS': '1000',
        }
        response = self.client.get(reverse('addFolder'), data)
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual(self.user4.username, context['user'].username)
        self.assertEqual('', context['folder'].name)
        self.assertEqual("admin/add_edit_folder.html", response.templates[0].name)

        newFolderName = 'testNewFolder'
        data['name'] = newFolderName
        data['localPath'] = '/data/newPath'
        data['viewOption'] = 'E'
        response = self.client.post(reverse('addFolder'), data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/folderAdmin/', response.url)

        newFolder = Folder.objects.get(name=newFolderName)
        self.assertEqual(newFolder.name, newFolderName)
        self.assertEqual('/data/newPath', newFolder.localPath)


class GroupTest(BaseAdminTest):
    def testGroupAdminView(self):
        self.login(self.user4)
        response = self.client.get(reverse('groupAdmin'))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual('admin/group_admin.html', response.templates[0].name)

        self.assertEqual(1, len(context['groups']))
        self.assertEqual(self.group1.name, context['groups'][0])

        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('groupAdmin'))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/groupAdmin/', response.url)

    def testAddGroup(self):
        self.login(self.user4)
        data = {'groupName': 'newGroupName'}
        response = self.client.post(reverse('addGroup'), data=data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/groupAdmin/', response.url)
        self.assertTrue(Group.objects.get(name='newGroupName'))

        # test add invalid group name
        data = {'groupName': 'new Group Name'}
        response = self.client.post(reverse('addGroup'), data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assert_message_contains(response, "Invalid group name.  Must only contain letters, numbers, and underscores")
        self.assertEqual('admin/group_admin.html', response.templates[0].name)
        self.assertFalse(get_object_or_None(Group, name='new Group Name'))

        self.logout()
        self.login(self.user1)
        data = {'groupName': 'newGroupName2'}
        response = self.client.post(reverse('addGroup'), data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('index.html', response.templates[0].name)
        self.assertFalse(get_object_or_None(Group, name='newGroupName2'))

    def testDeleteGroup(self):
        self.login(self.user1)
        args = [self.group1.name]
        response = self.client.post(reverse('deleteGroup', args=args))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/deleteGroup/%s' % self.group1.name, response.url)
        self.assertTrue(get_object_or_None(Group, name=self.group1.name))

        self.logout()
        self.login(self.user4)
        args = [self.group1.name]
        response = self.client.post(reverse('deleteGroup', args=args))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/groupAdmin/', response.url)
        self.assertFalse(get_object_or_None(Group, name=self.group1.name))

    def testEditGroup(self):
        self.login(self.user4)
        response = self.client.get(reverse('editGroup', args=[self.group1.name]))
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual(self.group1.name, context['groupName'])
        self.assertEqual("admin/edit_group.html", response.templates[0].name)

        userPk = str(User.objects.get(username=self.user3.username).pk)
        data = {'name': 'newGroupName',
                'users': userPk
                }
        self.assertFalse(User.objects.get(username=self.user3.username).groups.filter(name__in=['newGroupName']).exists())
        response = self.client.post(reverse('editGroup', args=[self.group1.name]), data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/groupAdmin/', response.url)
        self.assertEqual('newGroupName', Group.objects.get(pk=self.group1.pk).name)
        self.assertTrue(User.objects.get(username=self.user3.username).groups.filter(name__in=['newGroupName']).exists())
