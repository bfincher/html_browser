#!/usr/bin/python
import os
import unittest

if __name__=="__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "html_browser_site.settings")
    import django
    django.setup()
    from html_browser import test_utils
    
    testList = [test_utils.UtilsTest]
    testLoader = unittest.TestLoader()

    caseList = []
    for testCase in testList:
        testSuite = testLoader.loadTestsFromTestCase(testCase)
        caseList.append(testSuite)

    suite = unittest.TestSuite(caseList)
    runner = unittest.TextTestRunner()
    runner.run(suite)
