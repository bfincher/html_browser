import unittest

from html_browser.models import Folder
from html_browser.utils import getCheckedEntries, getCurrentDirEntries

class UtilsTest(unittest.TestCase):
    def testGetCheckedEntries(self):
        dic = {'cb-checkbox_1': 'on',
            'cb-checkbox_2': 'off',
            'cb-checkbox_3': 'on'}

        checkedEntries = getCheckedEntries(dic)
        self.assertEquals(2, len(checkedEntries))

    def testGetCurrentDirEntries(self):
        folder = Folder()
        folder.name='test'
        folder.localPath='html_browser/test_dir'
        folder.viewOption='E'
        folder.save()

        try:
            entries = getCurrentDirEntries(folder, '/', True)
            self.assertEquals(3, len(entries))

            entry = entries[0]
            self.assertTrue(entry.isDir)
            self.assertEquals('dir_a', entry.name)
            self.assertEquals(entry.name, entry.nameUrl)
            self.assertEquals('&nbsp', entry.size)
            self.assertEquals('2016-11-12 03:32:33 PM', entry.lastModifyTime)
            self.assertFalse(entry.hasThumbnail)
            self.assertIsNone(entry.thumbnailUrl)

            entry = entries[1]
            self.assertFalse(entry.isDir)
            self.assertEquals('file_a.txt', entry.name)
            self.assertEquals(entry.name, entry.nameUrl)
            self.assertEquals('20', entry.size)
            self.assertEquals(20, entry.sizeNumeric)
            self.assertEquals('2016-11-12 03:32:09 PM', entry.lastModifyTime)
            self.assertFalse(entry.hasThumbnail)
            self.assertIsNone(entry.thumbnailUrl)

            entry = entries[2]
            self.assertFalse(entry.isDir)
            self.assertEquals('file_b.txt', entry.name)
            self.assertEquals(entry.name, entry.nameUrl)
            self.assertEquals('26', entry.size)
            self.assertEquals(26, entry.sizeNumeric)
            self.assertEquals('2016-11-12 03:32:24 PM', entry.lastModifyTime)
            self.assertFalse(entry.hasThumbnail)
            self.assertIsNone(entry.thumbnailUrl)

        finally:
            folder.delete()

def main():
    unittest.main()

if __name__=="__main__":
    main()
