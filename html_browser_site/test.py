#from urllib import quote

import os
from django.contrib.auth.models import User
from html_browser.models import Folder
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

    folder = Folder.objects.filter(name='test folder')[0]
    print folder
    print folder.grouppermission_set.all()

if __name__ == '__main__':
    main()