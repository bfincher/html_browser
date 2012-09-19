
from django.utils import unittest
from django.contrib.auth.models import User
from html_browser.models import UserPermission, Folder


class SimpleTest(unittest.TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class PermissionTest(unittest.TestCase):
    def setUp(self):
        
        self.user1 = User()
        self.user1.username = 'unit_test_user1'
        self.user1.save()
        
        self.user2 = User()
        self.user2.username = 'unit test user2'
        self.user2.save()
        
        self.users = [self.user1, self.user2]
        
        self.folder1 = Folder()
        self.folder1.name = 'unit test folder1'
        self.folder1.save()
        
        self.folders = [self.folder1]
        
        self.userPerm1 = UserPermission()
        self.userPerm1.folder = self.folder1
        self.userPerm1.permission = 'R'
        self.userPerm1.user = self.user1
        self.userPerm1.save()
        
        self.userperms = [self.userPerm1]
    
    def tearDown(self):
        for user in self.users:
            user.delete()
            
        for folder in self.folders:
            folder.delete()
            
        for perm in self.userperms:
            perm.delete()        
        
    def testPermissions(self):        
        self.assertTrue(self.folder1.userCanRead(self.user1))
        self.assertTrue(self.folder1.userCanRead(self.user2))