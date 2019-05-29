from html_browser.views.test_base_view import contextCheck, BaseViewTest
from html_browser.utils import getFolderLinkDir
from html_browser.models import Folder
from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.urls import reverse
import logging
import os

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
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals('admin/admin.html', response.templates[0].name)
        
        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('admin'))
        self.assertEquals(302, response.status_code)
        
    def testFolderAdminView(self):
        self.login(self.user4)
        response = self.client.get(reverse('folderAdmin'))
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals('admin/folder_admin.html', response.templates[0].name)

        self.assertEquals(len(self.folders), len(context['folders']))
        self.assertEquals(self.folder1, context['folders'][0])
        self.assertEquals(self.folder2, context['folders'][1])
        self.assertEquals(self.folder3, context['folders'][2])
        self.assertEquals(self.folder4, context['folders'][3])
        
        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('folderAdmin'))
        self.assertEquals(302, response.status_code)
        
    def testDeleteFolder(self):
        folderLinkDir = getFolderLinkDir(self.folder2.name)
        if not os.path.exists(folderLinkDir):
            open(folderLinkDir, 'a').close()
            
        self.login(self.user4)
        args=[self.folder2.name]
        response = self.client.post(reverse('deleteFolder', args=args))
        self.assertEquals(302, response.status_code)
        self.assertFalse(os.path.exists(folderLinkDir))
        self.assertFalse(get_object_or_None(Folder, name=self.folder2.name))
        
        self.logout()
        self.login(self.user1)
        args = [self.folder3.name]
        response = self.client.post(reverse('deleteFolder', args=args))
        self.assertEquals(302, response.status_code)
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
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(self.user4.username, context['user'].username)
        self.assertEquals(self.folder1.name, context['folder'].name)
        self.assertEqual("admin/add_edit_folder.html", response.templates[0].name)
        
        
        # make sure the folder link dir exists for the folder so that we can ensure it changed
        folderLinkDir = getFolderLinkDir(self.folder1.name)
        if not os.path.exists(folderLinkDir):
            os.symlink(self.folder1.localPath, folderLinkDir)
            
        data['name'] = self.folder1.name
        data['localPath'] = '/data/newPath'
        data['viewOption'] = 'E'
        response = self.client.post(reverse('editFolder', args=[self.folder1.name]), data)
        self.assertEquals(302, response.status_code)
        self.assertEqual('/folderAdmin/', response.url)
        
        newFolder1 = Folder.objects.get(pk=self.folder1.pk)
        self.assertEqual(self.folder1.name, newFolder1.name)
        self.assertEqual('/data/newPath', newFolder1.localPath)
        self.assertTrue(os.path.exists(getFolderLinkDir(self.folder1.name)))
        self.assertEqual("/data/newPath", os.path.realpath(folderLinkDir))
        
        
        
