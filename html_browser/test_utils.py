import unittest

from html_browser.models import Folder
from html_browser.utils import getCheckedEntries, getCurrentDirEntries, FolderAndPath
from html_browser import utils

from datetime import datetime, timedelta
import os
from shutil import rmtree


class TestRequest():
    def __init__(self):
        self.GET = {}


class FolderAndPathTest(unittest.TestCase):
    def test(self):
        testDir = 'html_browser/test_dir'

        testDirAbsPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_dir/')

        folder = Folder()
        folder.name = 'test'
        folder.localPath = testDirAbsPath
        folder.viewOption = 'E'
        folder.save()

        try:
            folderAndPath = FolderAndPath(folder=folder, path='')
            self.assertEquals('test', folderAndPath.folder.name)
            self.assertEquals(testDirAbsPath, folderAndPath.absPath)
            self.assertEquals('', folderAndPath.relativePath)

            folderAndPath = FolderAndPath(folderName=folder.name, path='')
            self.assertEquals('test', folderAndPath.folder.name)
            self.assertEquals(testDirAbsPath, folderAndPath.absPath)
            self.assertEquals('', folderAndPath.relativePath)

            folderAndPath = FolderAndPath(url='%s/' % folder.name)
            self.assertEquals('test', folderAndPath.folder.name)
            self.assertEquals(testDirAbsPath, folderAndPath.absPath)
            self.assertEquals('', folderAndPath.relativePath)
        finally:
            folder.delete()


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

            entries = getCurrentDirEntries(FolderAndPath(folder=folder, path=''), True)
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


def main():
    unittest.main()

if __name__ == "__main__":
    main()
