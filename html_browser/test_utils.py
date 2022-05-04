import os
import re
import unittest
from datetime import datetime, timedelta
from shutil import rmtree

from html_browser import settings, utils
from html_browser._os import join_paths
from html_browser.constants import _constants as const
from html_browser.models import Folder
from html_browser.utils import \
    FolderAndPath, FolderAndPathArgumentException, NoParentException, Path, \
    get_checked_entries, format_bytes

thumbUrlRegex = re.compile(rf'^/{settings.URL_PREFIX}thumb/(cache/[0-9a-f]{{2}}/[0-9a-f]{{2}}/[0-9a-f]{{32}}\.jpg)$')


class FolderAndPathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testDirAbsPath = join_paths(os.path.dirname(settings.BASE_DIR_REALPATH), 'test_dir/')
        cls.folder = Folder()
        cls.folder.name = 'test'
        cls.folder.local_path = cls.testDirAbsPath
        cls.folder.view_option = 'E'
        cls.folder.save()

        cls.folder2 = Folder()
        cls.folder2.name = 'test2'
        cls.folder2.local_path = 'test_path'
        cls.folder2.save()

    @classmethod
    def tearDownClass(cls):
        cls.folder.delete()

    def __testConstruct(self, folder, path):
        expected_abs_path = join_paths(folder.local_path, path)
        expected_url = join_paths(folder.name, path)

        objs = [FolderAndPath(folder=folder, path=path),
                FolderAndPath(folder_name=folder.name, path=path),
                FolderAndPath(url=expected_url)]

        for folder_and_path in objs:
            self.assertEqual(folder.name, folder_and_path.folder.name)
            self.assertEqual(expected_abs_path, folder_and_path.abs_path)
            self.assertEqual(path, folder_and_path.relative_path)
            self.assertEqual(expected_url, folder_and_path.url)

    def testConstruct(self):
        self.__testConstruct(FolderAndPathTest.folder, '')
        self.__testConstruct(FolderAndPathTest.folder, 'test_path')

        # test special case
        folder_and_path = FolderAndPath(folder=FolderAndPathTest.folder, path=join_paths(FolderAndPathTest.testDirAbsPath, 'test_path'))
        self.assertEqual(FolderAndPathTest.folder.name, folder_and_path.folder.name)
        self.assertEqual(join_paths(FolderAndPathTest.testDirAbsPath, 'test_path'), folder_and_path.abs_path)
        self.assertEqual('test_path', folder_and_path.relative_path)

        try:
            FolderAndPath(unknownArg='')
            self.fail('ExpectedFolderAndPathArgumentException')
        except FolderAndPathArgumentException:
            pass

        try:
            FolderAndPath(url='url', unknownArg='')
            self.fail('ExpectedFolderAndPathArgumentException')
        except FolderAndPathArgumentException:
            pass

        try:
            FolderAndPath(folder=None, path='path', unknownArg='')
            self.fail('ExpectedFolderAndPathArgumentException')
        except FolderAndPathArgumentException:
            pass

        try:
            FolderAndPath(path='path', unknownArg='')
            self.fail('ExpectedFolderAndPathArgumentException')
        except FolderAndPathArgumentException:
            pass

    def testEq(self):
        fp1 = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')
        fp2 = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')

        self.assertTrue(fp1 == fp2)

        fp2 = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path3')
        self.assertFalse(fp1 == fp2)

        fp2 = FolderAndPath(folder=FolderAndPathTest.folder2, path='test_path1/test_path2')
        self.assertFalse(fp1 == fp2)

    def testJson(self):
        fp = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')
        json_str = fp.to_json()
        from_json = FolderAndPath.from_json(json_str)
        self.assertEqual(fp, from_json)

    def testStr(self):
        fp = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')
        _str = str(fp)

        expected_str = f"folder_name = {fp.folder.name}, relative_path = {fp.relative_path}, abs_path = {fp.abs_path}, url = {fp.url}"

        self.assertEqual(expected_str, _str)

    def testGetParent(self):
        fp = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')
        expected_parent = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1')
        parent = fp.get_parent()
        self.assertEqual(expected_parent, parent)

        expected_parent = FolderAndPath(folder=FolderAndPathTest.folder, path='')
        parent = parent.get_parent()
        self.assertEqual(expected_parent, parent)

        try:
            parent.get_parent()
            self.fail("Expected NoParentException")
        except NoParentException:
            pass


class FileEntry:
    def __init__(self, path, expected_size=None):
        self.path = Path(path)
        stat = self.path.stat()
        self.orig_time = stat.st_mtime
        self.expected_size = expected_size
        self.time_set_to = None

    def set_m_time(self, time):
        self.time_set_to = time
        os.utime(self.path.__str__(), (int(time.timestamp()), int(time.timestamp())))

    def restore_m_time(self):
        os.utime(self.path.__str__(), (int(self.orig_time), int(self.orig_time)))


class UtilsTest(unittest.TestCase):
    def testGetCheckedEntries(self):
        dic = {'cb-checkbox_1': 'on',
               'cb-checkbox_2': 'off',
               'cb-checkbox_3': 'on'}

        checked_entries = get_checked_entries(dic)
        self.assertEqual(2, len(checked_entries))

    def testGetCurrentDirEntriesContentFilter(self):
        folder = Folder()
        folder.name = 'test'
        folder.local_path = '.'
        folder.view_option = 'E'
        folder.save()

        try:
            folder_and_path = FolderAndPath(folder=folder, path='')
            entries = folder_and_path.get_dir_entries(False, const.thumbnails_view_type, '*.py')
            self.assertTrue(len(entries) > 0)
            for entry in entries:
                self.assertTrue(entry.is_dir or entry.name.endswith('.py'))
        finally:
            folder.delete()

    def testGetCurrentDirEntriesHidden(self):
        folder = Folder()
        folder.name = 'test'
        folder.local_path = '.'
        folder.view_option = 'E'
        folder.save()

        try:
            test_file = '.testFile.txt'
            with open(test_file, 'a', encoding='utf8'):
                pass
            folder_and_path = FolderAndPath(folder=folder, path='')
            entries = folder_and_path.get_dir_entries(False, const.thumbnails_view_type)
            for entry in entries:
                self.assertFalse(entry.name.startswith('.'))

            folder_and_path = FolderAndPath(folder=folder, path='')
            entries = folder_and_path.get_dir_entries(True, const.thumbnails_view_type)
            found_hidden_entry = False

            for entry in entries:
                if entry.name.startswith('.'):
                    found_hidden_entry = True
                    break

            self.assertTrue(found_hidden_entry)

        finally:
            folder.delete()
            os.remove(test_file)

    def testGetCurrentDirEntries(self):
        folder = Folder.create('test', 'media', 'E')
        folder.save()

        try:
            media_dir = join_paths(settings.BASE_DIR, 'media')
            test_files = [FileEntry(join_paths(media_dir, 'bootstrap'), '&nbsp'),
                          FileEntry(join_paths(media_dir, 'datatables'), '&nbsp'),
                          FileEntry(join_paths(media_dir, 'images'), '&nbsp'),
                          FileEntry(join_paths(media_dir, 'krajee'), '&nbsp'),
                          FileEntry(join_paths(media_dir, 'add_user.js'), '1.80 KB'),
                          ]

            try:
                next_time = datetime.now()
                for entry in test_files:
                    entry.set_m_time(next_time)
                    next_time = next_time + timedelta(seconds=1)

                folder_and_path = FolderAndPath(folder=folder, path='')
                entries = folder_and_path.get_dir_entries(False, const.thumbnails_view_type)

                self.assertEqual(16, len(entries))

                for i, test_file in enumerate(test_files):
                    entry = entries[i]
                    self.assertEqual(test_file.path.is_dir(), entry.is_dir)
                    self.assertEqual(test_file.path.name, entry.name)
                    self.assertEqual(entry.name, entry.name_url)
                    self.assertEqual(test_file.expected_size, entry.size)
                    self.assertEqual(test_files[i].time_set_to.strftime('%Y-%m-%d %I:%M:%S %p'), entry.last_modify_time)
                    self.assertFalse(entry.has_thumbnail)
                    self.assertIsNone(entry.get_thumbnail_url())
            finally:
                # set time back to orig
                for entry in test_files:
                    entry.restore_m_time()

            folder_and_path = FolderAndPath(folder=folder, path='images')
            entries = folder_and_path.get_dir_entries(False, const.thumbnails_view_type)
            self.assertEqual(20, len(entries))
            entry = entries[0]
            self.assertFalse(entry.is_dir)
            self.assertEqual('Add-Folder-icon.png', entry.name)
            self.assertEqual(entry.name, entry.name_url)
            self.assertEqual('1.96 KB', entry.size)
            self.assertTrue(entry.has_thumbnail)
            match = thumbUrlRegex.match(entry.get_thumbnail_url())
            self.assertTrue(match)
            self.assertTrue(os.path.exists(join_paths(settings.THUMBNAIL_CACHE_DIR, match.group(1))))

            entry = entries[3]
            self.assertFalse(entry.is_dir)
            self.assertEqual('Paste-icon.png', entry.name)
            self.assertEqual(entry.name, entry.name_url)
            self.assertEqual('1.80 KB', entry.size)
            self.assertEqual(1844, entry.size_numeric)
            # self.assertEqual(img_time.strftime('%Y-%m-%d %I:%M:%S %p'), entry.last_modify_time)
            self.assertTrue(entry.has_thumbnail)
            match = thumbUrlRegex.match(entry.get_thumbnail_url())
            self.assertTrue(match)
            self.assertTrue(os.path.exists(join_paths(settings.THUMBNAIL_CACHE_DIR, match.group(1))))

        finally:
            folder.delete()

    def testReplaceEscapedUrl(self):
        self.assertEqual("part1,part2&", utils.replace_escaped_url("part1(comma)part2(ampersand)"))

    def testHandleDelete(self):
        test_dir = 'html_browser/test_dir2'
        child_dir = join_paths(test_dir, 'child_dir')
        test_file_1 = join_paths(child_dir, 'test_file1.txt')
        test_file_2 = join_paths(child_dir, 'test_file2.txt')
        test_file_3 = join_paths(child_dir, 'test_file3.txt')

        folder = Folder.create(name='test', local_path=test_dir, view_option='E')
        folder.save()

        try:
            if os.path.isdir(test_dir):
                rmtree(test_dir)

            os.mkdir(test_dir)
            os.mkdir(child_dir)

            with open(test_file_1, 'w', encoding='utf8') as f:
                f.write('Hello World')
            with open(test_file_2, 'w', encoding='utf8') as f:
                f.write('Hello World')
            with open(test_file_3, 'w', encoding='utf8') as f:
                f.write('Hello World')

            entries = ['test_file2.txt', 'test_file1.txt']

            utils.handle_delete(FolderAndPath(folder=folder, path='child_dir'), entries)

            self.assertFalse(os.path.exists(test_file_1))
            self.assertFalse(os.path.exists(test_file_2))
            self.assertTrue(os.path.exists(test_file_3))

            entries = ['child_dir']
            utils.handle_delete(FolderAndPath(folder=folder, path=''), entries)
            self.assertFalse(os.path.exists(test_file_3))
            self.assertFalse(os.path.exists(child_dir))
        finally:
            folder.delete()

            if os.path.isdir(test_dir):
                rmtree(test_dir)

    def testFormatBytes(self):
        self.assertEqual("1.15 GB", format_bytes(1234567890))
        self.assertEqual("117.74 MB", format_bytes(123456789))
        self.assertEqual("120.56 KB", format_bytes(123456))
        self.assertEqual("123", format_bytes(123))

        self.assertEqual("1205632.71 KB", format_bytes(1234567890, force_unit='KB'))
        self.assertEqual("1205632.71", format_bytes(1234567890, force_unit='KB', include_unit_suffix=False))


def main():
    unittest.main()


if __name__ == "__main__":
    main()
