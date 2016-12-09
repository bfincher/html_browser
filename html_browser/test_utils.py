import unittest

from html_browser.models import Folder
from html_browser.utils import *
from html_browser.constants import _constants as const
from html_browser import utils

from datetime import datetime, timedelta
import os
from shutil import rmtree


class TestRequest():
    def __init__(self):
        self.GET = {}


class FolderAndPathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testDirAbsPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_dir/')
        cls.folder = Folder()
        cls.folder.name = 'test'
        cls.folder.localPath = cls.testDirAbsPath
        cls.folder.viewOption = 'E'
        cls.folder.save()

        cls.folder2 = Folder()
        cls.folder2.name = 'test2'
        cls.folder2.localPath = 'test_path'
        cls.folder2.save()

    @classmethod
    def tearDownClass(cls):
        cls.folder.delete()

    def __testConstruct(self, folder, path):
        expectedAbsPath = os.path.join(folder.localPath, path)
        expectedUrl = os.path.join(folder.name, path)

        objs = [FolderAndPath(folder=folder, path=path),
                FolderAndPath(folderName=folder.name, path=path),
                FolderAndPath(url=expectedUrl)]

        for folderAndPath in objs:
            self.assertEquals(folder.name, folderAndPath.folder.name)
            self.assertEquals(expectedAbsPath, folderAndPath.absPath)
            self.assertEquals(path, folderAndPath.relativePath)
            self.assertEquals(expectedUrl, folderAndPath.url)

    def testConstruct(self):
        testDir = 'html_browser/test_dir'

        self.__testConstruct(FolderAndPathTest.folder, '')
        self.__testConstruct(FolderAndPathTest.folder, 'test_path')

        # test special case
        folderAndPath = FolderAndPath(folder=FolderAndPathTest.folder, path=os.path.join(FolderAndPathTest.testDirAbsPath, 'test_path'))
        self.assertEquals(FolderAndPathTest.folder.name, folderAndPath.folder.name)
        self.assertEquals(os.path.join(FolderAndPathTest.testDirAbsPath, 'test_path'), folderAndPath.absPath)
        self.assertEquals('test_path', folderAndPath.relativePath)

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
        jsonStr = fp.toJson()
        fromJson = FolderAndPath.fromJson(jsonStr)
        self.assertEquals(fp, fromJson)

    def testStr(self):
        fp = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')
        _str = str(fp)

        expectedStr = "folder_name = %s, relativePath = %s, absPath = %s, url = %s" % (fp.folder.name, fp.relativePath, fp.absPath, fp.url)

        self.assertEquals(expectedStr, _str)

    def testGetParent(self):
        fp = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1/test_path2')
        expectedParent = FolderAndPath(folder=FolderAndPathTest.folder, path='test_path1')
        parent = fp.getParent()
        self.assertEquals(expectedParent, parent)

        expectedParent = FolderAndPath(folder=FolderAndPathTest.folder, path='')
        parent = parent.getParent()
        self.assertEquals(expectedParent, parent)

        try:
            parent.getParent()
            self.fail("Expected NoParentException")
        except NoParentException:
            pass


class UtilsTest(unittest.TestCase):
    def testGetCheckedEntries(self):
        dic = {'cb-checkbox_1': 'on',
               'cb-checkbox_2': 'off',
               'cb-checkbox_3': 'on'}

        checkedEntries = getCheckedEntries(dic)
        self.assertEquals(2, len(checkedEntries))

    def testGetCurrentDirEntries(self):
        folder = Folder()
        folder.name = 'test'
        folder.localPath = 'html_browser/test_dir'
        folder.viewOption = 'E'
        folder.save()

        try:
            dirA_time = datetime.now()
            os.utime('html_browser/test_dir/dir_a', (int(dirA_time.timestamp()), int(dirA_time.timestamp())))

            fileA_time = dirA_time + timedelta(seconds=1)
            os.utime('html_browser/test_dir/file_a.txt', (int(fileA_time.timestamp()), int(fileA_time.timestamp())))

            fileB_time = fileA_time + timedelta(seconds=1)
            os.utime('html_browser/test_dir/file_b.txt', (int(fileB_time.timestamp()), int(fileB_time.timestamp())))

            entries = getCurrentDirEntries(FolderAndPath(folder=folder, path=''), True, const.detailsViewType)
            self.assertEquals(3, len(entries))

            entry = entries[0]
            self.assertTrue(entry.isDir)
            self.assertEquals('dir_a', entry.name)
            self.assertEquals(entry.name, entry.nameUrl)
            self.assertEquals('&nbsp', entry.size)
            self.assertEquals(dirA_time.strftime('%Y-%m-%d %I:%M:%S %p'), entry.lastModifyTime)
            self.assertFalse(entry.hasThumbnail)
            self.assertIsNone(entry.thumbnailUrl)

            entry = entries[1]
            self.assertFalse(entry.isDir)
            self.assertEquals('file_a.txt', entry.name)
            self.assertEquals(entry.name, entry.nameUrl)
            self.assertEquals('20', entry.size)
            self.assertEquals(20, entry.sizeNumeric)
            self.assertEquals(fileA_time.strftime('%Y-%m-%d %I:%M:%S %p'), entry.lastModifyTime)
            self.assertFalse(entry.hasThumbnail)
            self.assertIsNone(entry.thumbnailUrl)

            entry = entries[2]
            self.assertFalse(entry.isDir)
            self.assertEquals('file_b.txt', entry.name)
            self.assertEquals(entry.name, entry.nameUrl)
            self.assertEquals('26', entry.size)
            self.assertEquals(26, entry.sizeNumeric)
            self.assertEquals(fileB_time.strftime('%Y-%m-%d %I:%M:%S %p'), entry.lastModifyTime)
            self.assertFalse(entry.hasThumbnail)
            self.assertIsNone(entry.thumbnailUrl)

        finally:
            folder.delete()

    def testReplaceEscapedUrl(self):
        self.assertEquals("part1,part2&", utils.replaceEscapedUrl("part1(comma)part2(ampersand)"))

    def testHandleDelete(self):
        testDir = 'html_browser/test_dir2'
        childDir = os.path.join(testDir, 'child_dir')
        testFile1 = os.path.join(childDir, 'test_file1.txt')
        testFile2 = os.path.join(childDir, 'test_file2.txt')
        testFile3 = os.path.join(childDir, 'test_file3.txt')

        folder = Folder()
        folder.name = 'test'
        folder.localPath = testDir
        folder.viewOption = 'E'
        folder.save()

        try:
            if os.path.isdir(testDir):
                rmtree(testDir)

            os.mkdir(testDir)
            os.mkdir(childDir)

            with open(testFile1, 'w') as f:
                f.write('Hello World')
            with open(testFile2, 'w') as f:
                f.write('Hello World')
            with open(testFile3, 'w') as f:
                f.write('Hello World')

            entries = ['test_file2.txt', 'test_file1.txt']

            utils.handleDelete(FolderAndPath(folder=folder, path='child_dir'), entries)

            self.assertFalse(os.path.exists(testFile1))
            self.assertFalse(os.path.exists(testFile2))
            self.assertTrue(os.path.exists(testFile3))

            entries = ['child_dir']
            utils.handleDelete(FolderAndPath(folder=folder, path=''), entries)
            self.assertFalse(os.path.exists(testFile3))
            self.assertFalse(os.path.exists(childDir))
        finally:
            folder.delete()

            if os.path.isdir(testDir):
                rmtree(testDir)

    def testFormatBytes(self):
       self.assertEquals("1.15 GB", formatBytes(1234567890))
       self.assertEquals("117.74 MB", formatBytes(123456789))
       self.assertEquals("120.56 KB", formatBytes(123456))
       self.assertEquals("123", formatBytes(123))

       self.assertEquals("1205632.71 KB", formatBytes(1234567890, forceUnit='KB'))
       self.assertEquals("1205632.71", formatBytes(1234567890, forceUnit='KB', includeUnitSuffix=False))


def main():
    unittest.main()

if __name__ == "__main__":
    main()
