
from django.contrib.auth.models import Group, User
from django.test import TestCase

from html_browser.models import (CAN_DELETE, CAN_READ, CAN_WRITE, Folder,
                                 GroupPermission, UserPermission)


class UserPermissionTest(TestCase):
    def setUp(self):

        self.user1 = User()
        self.user1.username = 'unit test user1'
        self.user1.save()

        self.user2 = User()
        self.user2.username = 'unit test user2'
        self.user2.save()

        self.user3 = User()
        self.user3.username = 'unit test user3'
        self.user3.save()

        self.user4 = User()
        self.user4.username = 'unit test user4'
        self.user4.save()

        self.user5 = User()
        self.user5.username = 'unit test user5'
        self.user5.is_superuser = True
        self.user5.save()

        self.users = [self.user1, self.user2, self.user3, self.user4, self.user5]

        self.folder1 = Folder()
        self.folder1.name = 'unit test folder1'
        self.folder1.save()

        self.folders = [self.folder1]

        self.userPerm1 = UserPermission()
        self.userPerm1.folder = self.folder1
        self.userPerm1.permission = CAN_READ
        self.userPerm1.user = self.user1
        self.userPerm1.save()

        self.userPerm2 = UserPermission()
        self.userPerm2.folder = self.folder1
        self.userPerm2.permission = CAN_WRITE
        self.userPerm2.user = self.user3
        self.userPerm2.save()

        self.userPerm3 = UserPermission()
        self.userPerm3.folder = self.folder1
        self.userPerm3.permission = CAN_DELETE
        self.userPerm3.user = self.user4
        self.userPerm3.save()

        self.userperms = [self.userPerm1, self.userPerm2, self.userPerm3]

    def tearDown(self):
        for user in self.users:
            user.delete()

        for folder in self.folders:
            folder.delete()

        for perm in self.userperms:
            perm.delete()

    def testPermissions(self):
        self.assertTrue(self.folder1.userCanRead(self.user1))
        self.assertFalse(self.folder1.userCanRead(self.user2))

        self.assertTrue(self.folder1.userCanRead(self.user3))
        self.assertTrue(self.folder1.userCanWrite(self.user3))
        self.assertFalse(self.folder1.userCanDelete(self.user3))

        self.assertTrue(self.folder1.userCanRead(self.user4))
        self.assertTrue(self.folder1.userCanWrite(self.user4))
        self.assertTrue(self.folder1.userCanDelete(self.user4))

        self.assertTrue(self.folder1.userCanRead(self.user5))
        self.assertTrue(self.folder1.userCanWrite(self.user5))
        self.assertTrue(self.folder1.userCanDelete(self.user5))


class GroupPermissionTest(TestCase):
    def setUp(self):

        self.group1 = Group()
        self.group1.name = "group test group1"
        self.group1.save()

        self.group2 = Group()
        self.group2.name = "group test group2"
        self.group2.save()

        self.group3 = Group()
        self.group3.name = "group test group3"
        self.group3.save()

        self.groups = [self.group1, self.group2, self.group3]

        self.user1 = User()
        self.user1.username = 'group test user1'
        self.user1.save()
        self.user1.groups.add(self.group1)
        self.user1.save()

        self.user2 = User()
        self.user2.username = 'group test user2'
        self.user2.save()

        self.user3 = User()
        self.user3.username = 'group test user3'
        self.user3.save()
        self.user3.groups.add(self.group2)
        self.user3.save()

        self.user4 = User()
        self.user4.username = 'group test user4'
        self.user4.save()
        self.user4.groups.add(self.group3)
        self.user4.save()

        self.users = [self.user1, self.user2, self.user3, self.user4]

        self.folder1 = Folder()
        self.folder1.name = 'group test folder1'
        self.folder1.save()

        self.folders = [self.folder1]

        self.groupPerm1 = GroupPermission()
        self.groupPerm1.folder = self.folder1
        self.groupPerm1.permission = CAN_READ
        self.groupPerm1.group = self.group1
        self.groupPerm1.save()

        self.groupPerm2 = GroupPermission()
        self.groupPerm2.folder = self.folder1
        self.groupPerm2.permission = CAN_WRITE
        self.groupPerm2.group = self.group2
        self.groupPerm2.save()

        self.groupPerm3 = GroupPermission()
        self.groupPerm3.folder = self.folder1
        self.groupPerm3.permission = CAN_DELETE
        self.groupPerm3.group = self.group3
        self.groupPerm3.save()

        self.userperms = [self.groupPerm1, self.groupPerm2, self.groupPerm3]

    def tearDown(self):
        for user in self.users:
            user.delete()

        for group in self.groups:
            group.delete()

        for folder in self.folders:
            folder.delete()

        for perm in self.userperms:
            perm.delete()

    def testPermissions(self):
        self.assertTrue(self.folder1.userCanRead(self.user1))
        self.assertFalse(self.folder1.userCanRead(self.user2))

        self.assertTrue(self.folder1.userCanRead(self.user3))
        self.assertTrue(self.folder1.userCanWrite(self.user3))
        self.assertFalse(self.folder1.userCanDelete(self.user3))

        self.assertTrue(self.folder1.userCanRead(self.user4))
        self.assertTrue(self.folder1.userCanWrite(self.user4))
        self.assertTrue(self.folder1.userCanDelete(self.user4))
