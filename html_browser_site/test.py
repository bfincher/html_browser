#from urllib import quote

import os
from django.contrib.auth.models import User
from html_browser.models import Folder
from zipfile import ZipFile, ZIP_STORED
import zipfile
from tempfile import NamedTemporaryFile
from glob import glob
    
def addFolderToZip(zipFile, folder):
    __addFolderToZip__(zipFile, folder, folder)    
        
def __addFolderToZip__(zipFile, folder, basePath):
    for f in glob(folder + "/*"):
        if os.path.isfile(f):
            print(f)
            arcName = f.replace(basePath, '')
            zipFile.write(f, arcName, compress_type=zipfile.ZIP_DEFLATED)
        elif os.path.isdir(f):
            __addFolderToZip__(zipFile, f, basePath)


def main():
#    print quote('hello world;')
#    print 'hello'
#    from html_browser.models import Folder
#    
#    folder = Folder.objects.all()[0]
#    print folder.getNameAsHtml()
#    print folder
##    print folder.grouppermission_set
#    perm = folder.userpermission_set.filter(user__username='bfincher')[0]
#    print perm
#    print perm.canRead()
#    
#    folder = Folder.objects.filter(name='test folder;')[0]
#    print folder
#    
#    s = 'brian'
#    s = s[0:-1]
#    print s

#    folder = Folder.objects.filter(name='test folder')[0]
#    print folder
#    print folder.grouppermission_set.all()

##    tempFile = NamedTemporaryFile(mode='w', suffix='.zip', prefix='download', delete=False)
#    zipFile = ZipFile('c:/temp/zip.zip', mode='w')
##    zipFile.write('c:/tmp/fs_content/10.241.131.200.rfp', compress_type=zipfile.ZIP_DEFLATED)
#    addFolderToZip(zipFile, 'c:/tmp')
#    
#    zipFile.close()
#    print zipFile.infolist()

    list = []
    list.append((1, 2))
    print(len(list))
    print(list[0][1])
    list.pop(0)
    print(len(list))

if __name__ == '__main__':
    main()
