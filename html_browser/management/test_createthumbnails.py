import unittest
from html_browser import settings
from html_browser.utils import joinPaths
from html_browser.models import Folder
from sorl.thumbnail.models import KVStore
from django.core.management import call_command
from io import StringIO
import os
import re
import shutil

testDir = joinPaths(settings.BASE_DIR, 'test_image_dir')
srcImgDir = joinPaths(settings.BASE_DIR, 'media', 'images')


class ExpectedImage(object):
    def __init__(self, fileName, destDir):
        self.fileName = fileName
        self.srcPath = joinPaths(srcImgDir, fileName)
        self.destPath = joinPaths(testDir, destDir, fileName)


class TestCreateThumbnails(unittest.TestCase):

    testThumbnailsDir = joinPaths(settings.BASE_DIR, 'test_thumbnails')
    origThumbnailsDir = settings.THUMBNAIL_CACHE_DIR
    expectedImages = []

    @classmethod
    def setUpClass(cls):
        settings.THUMBNAIL_CACHE_DIR = cls.testThumbnailsDir

        if os.path.exists(testDir):
            shutil.rmtree(testDir)
        if os.path.exists(cls.testThumbnailsDir):
            shutil.rmtree(cls.testThumbnailsDir)

        os.makedirs(joinPaths(testDir, 'a', 'aa'))
        os.makedirs(joinPaths(testDir, 'b'))
        os.makedirs(joinPaths(testDir, 'c'))

        cls.expectedImages = [ExpectedImage('Add-Folder-icon.png', 'a'),
                              ExpectedImage('ai-genericfile-icon.png', 'a'),
                              ExpectedImage('Copy-icon.png', 'a/aa'),
                              ExpectedImage('cut-icon.png', 'b'),
                              ExpectedImage('Document-icon.png', 'c')]

        for expectedImage in cls.expectedImages:
            shutil.copy(expectedImage.srcPath, expectedImage.destPath)

        # copy a file that should be ignored by thumbnail
        shutil.copy(joinPaths(srcImgDir, 'addgroupbackground.gif'), joinPaths(testDir, 'c'))

    @classmethod
    def tearDownClass(cls):
        settings.THUMBNAIL_CACHE_DIR = cls.origThumbnailsDir
        shutil.rmtree(testDir)
        if os.path.exists(cls.testThumbnailsDir):
            shutil.rmtree(cls.testThumbnailsDir)

    def setUp(self):
        Folder.objects.all().delete()
        KVStore.objects.all().delete()
        folder = Folder()
        folder.name = 'test_folder'
        folder.localPath = joinPaths(testDir)
        folder.save()

    def tearDown(self):
        Folder.objects.all().delete()
        KVStore.objects.all().delete()

    def test(self):
        self.assertEqual(0, KVStore.objects.count())
        out = StringIO()
        call_command('createthumbnails', 'test_folder', stdout=out)
        for expectedImg in TestCreateThumbnails.expectedImages:
            self.assertIn("Creating thumbnail for %s" % expectedImg.destPath, out.getvalue())

        thumbnailKeyRegex = re.compile(r'sorl-thumbnail\|\|thumbnails\|\|(\w+)')
        thumbnailKeysFound = 0
        for key in KVStore.objects.all():
            match = thumbnailKeyRegex.match(str(key))
            if match:
                thumbnailKeysFound += 1
        self.assertEqual(len(TestCreateThumbnails.expectedImages), thumbnailKeysFound)

        thumbnailFilesFound = 0
        for _, _, fileList in os.walk(TestCreateThumbnails.testThumbnailsDir):
            thumbnailFilesFound += len(fileList)

        self.assertEqual(len(TestCreateThumbnails.expectedImages), thumbnailFilesFound)
