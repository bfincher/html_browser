import json
from pathlib import Path
import os

from django.contrib.auth.models import Group, User
from django.test import TestCase

from html_browser.models import (CAN_DELETE, CAN_READ, CAN_WRITE, Folder,
                                 GroupPermission, UserPermission)
from html_browser._os import join_paths
from html_browser import settings


class ExtraSettingsTest(TestCase):
    def setUp(self):
        self.origUrlPrefix = settings.URL_PREFIX
        extraConfigDir = Path(settings.EXTRA_CONFIG_DIR)
        if not extraConfigDir.exists():
            extraConfigDir.mkdir(parents=True)

        self.localSettingsFile: Path = extraConfigDir.joinpath("local_settings.json")
        self.localSettingsCopy: Path = None
        if self.localSettingsFile.exists():
            self.localSettingsCopy = extraConfigDir.joinpath('local_settings_copy_for_test.json')
            self.localSettingsCopy.write_bytes(self.localSettingsFile.read_bytes())

        data = {}
        data['ALLOWED_HOSTS'] = ['host1', 'host2']
        data['URL_PREFIX'] = 'testPrefix'
        data['DEBUG'] = 'True'
        with open(self.localSettingsFile, 'w', encoding='utf8') as outfile:
            json.dump(data, outfile)

        settings.readExtraSettings()

    def tearDown(self):
        localSettingsFile = join_paths(settings.EXTRA_CONFIG_DIR, 'local_settings.json')
        os.remove(localSettingsFile)
        settings.URL_PREFIX = self.origUrlPrefix

        if self.localSettingsCopy:
            self.localSettingsFile.write_bytes(self.localSettingsCopy.read_bytes())
            self.localSettingsCopy.unlink()

    def test(self):
        self.assertTrue(len(settings.ALLOWED_HOSTS) > 2)
        self.assertTrue('host1' in settings.ALLOWED_HOSTS)
        self.assertTrue('host2' in settings.ALLOWED_HOSTS)
        self.assertEqual('testPrefix', settings.URL_PREFIX)
        self.assertTrue(settings.DEBUG)


class UserPermissionTest(TestCase): # pylint: disable=too-many-instance-attributes
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

    def tear_down(self):
        for user in self.users:
            user.delete()

        for folder in self.folders:
            folder.delete()

        for perm in self.userperms:
            perm.delete()

    def test_permissions(self):
        self.assertTrue(self.folder1.user_can_read(self.user1))
        self.assertFalse(self.folder1.user_can_read(self.user2))

        self.assertTrue(self.folder1.user_can_read(self.user3))
        self.assertTrue(self.folder1.user_can_write(self.user3))
        self.assertFalse(self.folder1.user_can_delete(self.user3))

        self.assertTrue(self.folder1.user_can_read(self.user4))
        self.assertTrue(self.folder1.user_can_write(self.user4))
        self.assertTrue(self.folder1.user_can_delete(self.user4))

        self.assertTrue(self.folder1.user_can_read(self.user5))
        self.assertTrue(self.folder1.user_can_write(self.user5))
        self.assertTrue(self.folder1.user_can_delete(self.user5))


class GroupPermissionTest(TestCase): # pylint: disable=too-many-instance-attributes
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
        self.user1.groups.add(self.group1) # pylint: disable=no-member
        self.user1.save()

        self.user2 = User()
        self.user2.username = 'group test user2'
        self.user2.save()

        self.user3 = User()
        self.user3.username = 'group test user3'
        self.user3.save()
        self.user3.groups.add(self.group2) # pylint: disable=no-member
        self.user3.save()

        self.user4 = User()
        self.user4.username = 'group test user4'
        self.user4.save()
        self.user4.groups.add(self.group3) # pylint: disable=no-member
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

    def tear_down(self):
        for user in self.users:
            user.delete()

        for group in self.groups:
            group.delete()

        for folder in self.folders:
            folder.delete()

        for perm in self.userperms:
            perm.delete()

    def test_permissions(self):
        self.assertTrue(self.folder1.user_can_read(self.user1))
        self.assertFalse(self.folder1.user_can_read(self.user2))

        self.assertTrue(self.folder1.user_can_read(self.user3))
        self.assertTrue(self.folder1.user_can_write(self.user3))
        self.assertFalse(self.folder1.user_can_delete(self.user3))

        self.assertTrue(self.folder1.user_can_read(self.user4))
        self.assertTrue(self.folder1.user_can_write(self.user4))
        self.assertTrue(self.folder1.user_can_delete(self.user4))
