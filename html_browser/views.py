from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from html_browser.models import Folder
from django.contrib.auth import login as auth_login, logout as auth_logout
from utils import getParentDirLink
from html_browser.utils import getCurrentDirEntries
from constants import _constants as const
from django.contrib.auth import authenticate

def index(request, errorText=None):
    allFolders = Folder.objects.all()
    folders = []
    for folder in allFolders:
        if folder.userCanRead(request.user):
            folders.append(folder)
            
    c = RequestContext(request, {'folders' : folders,
         'user' : request.user,
         'errorText' : errorText})
    
    return render_to_response('index.html', c)
    
#    return render_to_response('index.html',
#        {'folders' : folders,
#         'user' : request.user,
#         'errorText' : errorText}
#    )

def hbLogin(request):
    userName = request.POST['userName']
    password = request.POST['password']
    
    errorText = None
    
    user = authenticate(username=userName, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
        else:
            errorText = 'Account has been disabled'
    else:
        errorText = 'Invalid login'
    
    return redirect(const.BASE_URL, errorText)

#    return login(request, redirect_field_name='next', current_app='html_browser')

def hbLogout(request):
    auth_logout(request)
    return redirect(const.BASE_URL)

def content(request):
    currentFolder = request.GET['currentFolder']
    currentPath = request.GET['currentPath']
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    userCanWrite = userCanDelete or folder.userCanWrite(request.user)
    userCanRead = userCanWrite or folder.userCanRead(request.user)
    
    parentDirLink = getParentDirLink(currentPath, currentFolder)
    
    currentDirEntries = getCurrentDirEntries(folder, currentPath)
    
    status = ''
    
    return render_to_response('content_detail.html',
        {'currentFolder' : currentFolder,
         'currentPath' : currentPath,
         'userCanRead' : userCanRead,
         'userCanWrite' : userCanWrite,
         'userCanDelete' : userCanDelete,
         'parentDirLink' : parentDirLink,
         'status' : status,
         'viewTypes' : const.viewTypes,
         'currentDirEntries' : currentDirEntries,
         'constants' : const
         })

def hbChangePassword(request):
    c = RequestContext(request, {'constants' : const})
    return render_to_response('registration/change_password.html', c)

def hbChangePasswordResult(request):
    user = request.user
    errorMessage = None
    if user.check_password(request.POST['password']):
        newPw = request.POST['newPassword']
        confirmPw = request.POST['newPassword2']
        
        if newPw == confirmPw:
            user.set_password(newPw)
            user.save()
        else:
            errorMessage = "Passwords don't match"
    else:
        errorMessage = "Incorrect current password"
        
    if errorMessage == None:
        c = RequestContext(request, {'constants' : const})
        return render_to_response('registration/change_password_success.html', c)
    else:
        c = RequestContext(request, {'errorMessage' : errorMessage,
                                     'constants' : const})
        return render_to_response('registration/change_password_fail.html', c)