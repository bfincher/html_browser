
from django.utils import unittest
from django.contrib.auth.models import User
from html_browser.models import UserPermission, Folder


class PermissionTest(unittest.TestCase):
    def setUp(self):
        
        self.user1 = User()
        self.user1.username = 'unit_test_user1'
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
        
        
        self.users = [self.user1, self.user2, self.user3, self.user4]
        
        self.folder1 = Folder()
        self.folder1.name = 'unit test folder1'
        self.folder1.save()
        
        self.folders = [self.folder1]
        
        self.userPerm1 = UserPermission()
        self.userPerm1.folder = self.folder1
        self.userPerm1.permission = 'R'
        self.userPerm1.user = self.user1
        self.userPerm1.save()
        
        self.userPerm2 = UserPermission()
        self.userPerm2.folder = self.folder1
        self.userPerm2.permission = 'W'
        self.userPerm2.user = self.user3
        self.userPerm2.save()
        
        self.userPerm3 = UserPermission()
        self.userPerm3.folder = self.folder1
        self.userPerm3.permission = 'D'
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