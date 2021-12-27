import os
import re
import shutil
import unittest
from io import StringIO

from django.core.management import call_command
from sorl.thumbnail.models import KVStore

from html_browser import settings
from html_browser.models import Folder
from html_browser.utils import join_paths

test_dir = join_paths(settings.BASE_DIR, 'test_image_dir')
src_img_dir = join_paths(settings.BASE_DIR, 'media', 'images')


class ExpectedImage:
    def __init__(self, file_name, dest_dir):
        self.file_name = file_name
        self.src_path = join_paths(src_img_dir, file_name)
        self.dest_path = join_paths(test_dir, dest_dir, file_name)


class TestCreateThumbnails(unittest.TestCase):

    test_thumbnails_dir = join_paths(settings.BASE_DIR, 'test_thumbnails')
    orig_thumbnails_dir = settings.THUMBNAIL_CACHE_DIR
    expected_images = []

    @classmethod
    def setUpClass(cls):
        settings.THUMBNAIL_CACHE_DIR = cls.test_thumbnails_dir

        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        if os.path.exists(cls.test_thumbnails_dir):
            shutil.rmtree(cls.test_thumbnails_dir)

        os.makedirs(join_paths(test_dir, 'a', 'aa'))
        os.makedirs(join_paths(test_dir, 'b'))
        os.makedirs(join_paths(test_dir, 'c'))

        cls.expected_images = [ExpectedImage('Add-Folder-icon.png', 'a'),
                               ExpectedImage('ai-genericfile-icon.png', 'a'),
                               ExpectedImage('Copy-icon.png', 'a/aa'),
                               ExpectedImage('cut-icon.png', 'b'),
                               ExpectedImage('Document-icon.png', 'c')]

        for expected_image in cls.expected_images:
            shutil.copy(expected_image.src_path, expected_image.dest_path)

        # copy a file that should be ignored by thumbnail
        shutil.copy(join_paths(src_img_dir, 'addgroupbackground.gif'), join_paths(test_dir, 'c'))

    @classmethod
    def tearDownClass(cls):
        settings.THUMBNAIL_CACHE_DIR = cls.orig_thumbnails_dir
        shutil.rmtree(test_dir)
        if os.path.exists(cls.test_thumbnails_dir):
            shutil.rmtree(cls.test_thumbnails_dir)

    def setUp(self):
        Folder.objects.all().delete()
        KVStore.objects.all().delete()
        folder = Folder()
        folder.name = 'test_folder'
        folder.local_path = join_paths(test_dir)
        folder.save()

    def tearDown(self):
        Folder.objects.all().delete()
        KVStore.objects.all().delete()

    def test(self):
        self.assertEqual(0, KVStore.objects.count())
        out = StringIO()
        call_command('createthumbnails', 'test_folder', stdout=out)
        for expected_image in TestCreateThumbnails.expected_images:
            self.assertIn(f"Creating thumbnail for {expected_image.dest_path}", out.getvalue())

        thumbnail_key_regex = re.compile(r'sorl-thumbnail\|\|thumbnails\|\|(\w+)')
        thumbnail_keys_found = 0
        for key in KVStore.objects.all():
            match = thumbnail_key_regex.match(str(key))
            if match:
                thumbnail_keys_found += 1
        self.assertEqual(len(TestCreateThumbnails.expected_images), thumbnail_keys_found)

        thumbnail_files_found = 0
        for _, _, file_list in os.walk(TestCreateThumbnails.test_thumbnails_dir):
            thumbnail_files_found += len(file_list)

        self.assertEqual(len(TestCreateThumbnails.expected_images), thumbnail_files_found)
