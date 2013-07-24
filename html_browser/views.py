from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from html_browser.models import Folder, UserPermission, GroupPermission
from django.contrib.auth import login as auth_login, logout as auth_logout
from utils import getParentDirLink
import html_browser.utils
from html_browser.utils import getCurrentDirEntries, getCurrentDirEntriesSearch, Clipboard, handlePaste, handleDelete,\
    getPath, handleRename, handleDownloadZip, deleteOldFiles,\
    handleFileUpload, handleZipUpload, getDiskPercentFree, getPath,\
    getDiskUsageFormatted, handleAddUser, handleEditUser, handleDeleteUser,\
    handleAddGroup, handleDeleteGroup, \
    handleEditFolder, handleAddFolder, handleDeleteFolder
from constants import _constants as const
from django.contrib.auth import authenticate
from sendfile import sendfile
import os
from django.http import HttpResponse
import logging
from django.contrib.auth.models import User, Group

reqLogger = logging.getLogger('django.request')

def index(request):
    reqLogger.info('index ')
    reqLogger.debug(str(request))

    errorText = None
    if request.REQUEST.has_key('errorText'):
        errorText = request.REQUEST['errorText']

    allFolders = Folder.objects.all()
    folders = []
    for folder in allFolders:
        if folder.userCanRead(request.user):
            folders.append(folder)
            
    c = RequestContext(request, {'folders' : folders,
         'user' : request.user,
         'errorText' : errorText,
         'const' : const})
    
    return render_to_response('index.html', c)

def hbLogin(request):
    userName = request.POST['userName']
    password = request.POST['password']

    reqLogger.info("hbLogin")
    if userName is not None:
        reqLogger.info("userName = " + userName)
    
    errorText = None
    
    user = authenticate(username=userName, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            reqLogger.debug("%s authenticated", user)
        else:
            reqLogger.warn("%s attempted to log in to a disabled account", user)
            errorText = 'Account has been disabled'
    else:
        errorText = 'Invalid login'
        reqLogger.error("empty userName")
    
    redirectUrl = const.BASE_URL

    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=" + errorText
    return redirect(redirectUrl)


def hbLogout(request):
    reqLogger.info("user %s logged out", request.user)
    auth_logout(request)
    return redirect(const.BASE_URL)

def content(request):    
    reqLogger.info("content")
    reqLogger.debug(str(request))
    deleteOldFiles()
    
    currentFolder = request.REQUEST['currentFolder']
    currentPath = request.REQUEST['currentPath']        
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    userCanWrite = userCanDelete or folder.userCanWrite(request.user)
    userCanRead = userCanWrite or folder.userCanRead(request.user)    
    
    if userCanRead == False:
        reqLogger.warn("%s not allowed to read %s", request.user, currentFolder)
        return redirect(const.BASE_URL, 'You are not authorized to view this page')
    
    status = ''

    if request.REQUEST.has_key('action'):        
        action = request.REQUEST['action']
        if action == 'copyToClipboard':
            entries = request.REQUEST['entries']
            request.session['clipboard'] = Clipboard(currentFolder, currentPath, entries, 'COPY')            
            status='Items copied to clipboard';
        elif action == 'cutToClipboard':
            if not userCanDelete:
                status="You don't have delete permission on this folder"
            else:
                entries = request.REQUEST['entries']
                request.session['clipboard'] = Clipboard(currentFolder, currentPath, entries, 'CUT')            
                status = 'Items copied to clipboard'
        elif action == 'pasteFromClipboard':
            if not userCanWrite:
                status = "You don't have write permission on this folder"
            else:
                handlePaste(currentFolder, currentPath, request.session['clipboard'])
                status = 'Items pasted'
        elif action == 'deleteEntry':
            if not userCanDelete:
                status = "You don't have delete permission on this folder"
            else:
                handleDelete(folder, currentPath, request.REQUEST['entries'])
                status = 'File(s) deleted'
        elif action=='setViewType':
            viewType = request.REQUEST['viewType']
            request.session['viewType'] = viewType
        elif action == 'mkDir':
            dirName = request.REQUEST['dir']
            os.makedirs(getPath(folder.localPath, currentPath) + dirName)
        elif action == 'rename':
            handleRename(folder, currentPath, request.REQUEST['file'], request.REQUEST['newName'])
        else:
            raise RuntimeError('Unknown action ' + action)
        
        redirectUrl = const.CONTENT_URL + "?currentFolder=" + currentFolder + "&currentPath=" + currentPath + "&status=" + status
        return redirect(redirectUrl)        
    
    parentDirLink = getParentDirLink(currentPath, currentFolder)
    
    if request.REQUEST.has_key('status'):
        status = request.REQUEST['status']
    else:
        status = ''

    filter = None
    if request.REQUEST.has_key('filter'):
        filter = request.REQUEST['filter']
        status = status + ' Filtered on ' + request.REQUEST['filter']

    if request.REQUEST.has_key('search'):
        search = request.REQUEST['search']
        currentDirEntries= getCurrentDirEntriesSearch(folder, currentPath, search)

        c = RequestContext(request,
            {'currentFolder' : currentFolder,
             'currentPath' : currentPath,
             'userCanRead' : str(userCanRead).lower(),
             'userCanWrite' : str(userCanWrite).lower(),
             'userCanDelete' : str(userCanDelete).lower(),
             'status' : status,
             'currentDirEntries' : currentDirEntries,
             'const' : const,
             'user' : request.user,
         })
        return render_to_response("content_search.html", c)

    currentDirEntries = getCurrentDirEntries(folder, currentPath, filter)
    
    if request.session.has_key('viewType'):
        viewType = request.session['viewType']
    else:
        viewType = const.viewTypes[0]                   

    diskFreePct = getDiskPercentFree(getPath(folder.localPath, currentPath))
    diskUsage = getDiskUsageFormatted(getPath(folder.localPath, currentPath))

    c = RequestContext(request,
        {'currentFolder' : currentFolder,
         'currentPath' : currentPath,
         'userCanRead' : str(userCanRead).lower(),
         'userCanWrite' : str(userCanWrite).lower(),
         'userCanDelete' : str(userCanDelete).lower(),
         'parentDirLink' : parentDirLink,
         'status' : status,
         'viewTypes' : const.viewTypes,
         'selectedViewType' : viewType,
         'currentDirEntries' : currentDirEntries,
         'const' : const,
         'user' : request.user,
	 'diskFreePct' : diskFreePct,
	 'diskFree' : diskUsage.freeformatted,
	 'diskUsed' : diskUsage.usedformatted,
	 'diskTotal' : diskUsage.totalformatted,
         'diskUnit' : diskUsage.unit,
	 'showContent' : True,
         })
    
    if viewType == const.detailsViewType:
        template = 'content_detail.html'
    elif viewType == const.listViewType:
        template = 'content_list.html'
    else:
        template = 'content_thumbnail.html'
    return render_to_response(template, c)

def hbAdmin(request):
    reqLogger.info("admin")

    c = RequestContext(request, 
        {'const' : const,
         'user' : request.user
        })
    return render_to_response('admin/admin.html', c)

def folderAdminAction(request):
    reqLogger.info("folderAdminAction %s", request)

    errorText = None

    if request.REQUEST['submit'] == "Save":
        action = request.REQUEST['action']
        if action == 'addFolder':
            errorText = handleAddFolder(request)
        elif action == 'editFolder':
            handleEditFolder(request)
        elif action == 'deleteFolder':
            handleDeleteFolder(request)
        else:
            raise RuntimeError('Unknown action ' + action)

    redirectUrl = const.BASE_URL + "folderAdmin/"
    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=" + errorText

    return redirect(redirectUrl)           
    pass

def folderAdmin(request):
    reqLogger.info("folderAdmin")

    c = RequestContext(request,
        {'const' : const,
         'folders' : Folder.objects.all(),
        })
    return render_to_response('admin/folder_admin.html', c)

def addFolder(request):
    pass

def editFolder(request):
    reqLogger.info("editFolder: %s", request)

    folderName = request.REQUEST['name']
    folder = Folder.objects.get(name = folderName)

    userIds = []
    userPerms = UserPermission.objects.filter(folder=folder)
    for perm in userPerms:
        userIds.append(perm.user.id)

    usersNotInFolder = User.objects.exclude(id__in = userIds)

    groupIds = []
    groupPerms = GroupPermission.objects.filter(folder=folder)
    for perm in groupPerms:
        groupIds.append(perm.group.id)

    groupsNotInFolder = Group.objects.exclude(id__in = groupIds)

    c = RequestContext(request,
        {'const' : const,
	 'folder' : folder,
         'usersNotAssignedToFolder' : usersNotInFolder,
         'groupsNotAssignedToFolder' : groupsNotInFolder,
	 'groupPermissions' : groupPerms,
	 'userPermissions' : userPerms,
        })
    return render_to_response('admin/edit_folder.html', c)

def groupAdminAction(request):
    reqLogger.info("groupAdminAction %s", request)

    errorText = None

    if request.REQUEST['submit'] == "Save":
        action = request.REQUEST['action']
        if action == 'addGroup':
            errorText = handleAddGroup(request)
        elif action == 'deleteGroup':
            handleDeleteGroup(request)
        else:
            raise RuntimeError('Unknown action ' + action)

    redirectUrl = const.BASE_URL + "groupAdmin/"
    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=" + errorText

    return redirect(redirectUrl)           

def groupAdmin(request):
    reqLogger.info("groupAdmin")

    groups = []
    for group in Group.objects.all():
        groups.append(group.name)

    c = RequestContext(request, 
        {'const' : const,
         'groups' : groups,
        })
    return render_to_response('admin/group_admin.html', c)

def userAdminAction(request):
    reqLogger.info("userAdminAction %s", request)
    errorText = None

    if request.REQUEST['submit'] == "Save":
        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        action = request.REQUEST['action']
        if action == 'editUser':
            handleEditUser(request.POST)
        elif action == 'addUser':
            errorText = handleAddUser(request.POST)
        elif action == 'deleteUser':
            handleDeleteUser(request)
        else:
            raise RuntimeError('Unknown action ' + action)

    redirectUrl = const.BASE_URL + "userAdmin/"
    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=" + errorText

    return redirect(redirectUrl)           

def userAdmin(request):
    reqLogger.info("userAdmins")

    if not request.user.is_staff:
        raise RuntimeError("User is not an admin")

    c = RequestContext(request, 
        {'const' : const,
         'users' : User.objects.all(),
        })
    return render_to_response('admin/user_admin.html', c)

def editUser(request):
    if not request.user.is_staff:
        raise RuntimeError("User is not an admin")

    userName = request.REQUEST['userName']
    reqLogger.info("editUser: user = %s", userName)

    editUser = User.objects.get(username=userName)

    activeGroupNames = []
    groupNames = []

    for group in editUser.groups.all():
        activeGroupNames.append(group.name)

    for group in Group.objects.exclude(id__in = editUser.groups.all().values_list('id', flat=True)):
        groupNames.append(group.name)

    c = RequestContext(request, 
        {'const' : const,
         'editUser' : editUser,
         'activeGroupNames' : activeGroupNames,
         'groupNames' : groupNames,
        })
    return render_to_response('admin/edit_user.html', c)

def addUser(request):
    reqLogger.info("addUser")

    if not request.user.is_staff:
        raise RuntimeError("User is not an admin")

    groupNames = []

    for group in Group.objects.all():
        groupNames.append(group.name)

    c = RequestContext(request, 
        {'const' : const,
         'groupNames' : groupNames,
        })

    return render_to_response('admin/add_user.html', c)

def hbChangePassword(request):
    reqLogger.info("hbChangePassword")
    c = RequestContext(request, 
        {'const' : const,
         'user' : request.user
        })
    return render_to_response('admin/change_password.html', c)

def hbChangePasswordResult(request):
    user = request.user
    reqLogger.info("hbChangePasswordResult: user = %s", user)
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
        c = RequestContext(request, 
	    {'const' : const,
	     'user' : request.user,
	    })
	reqLogger.info("success")
        return render_to_response('admin/change_password_success.html', c)
    else:
        reqLogger.warn(errorMessage)
        c = RequestContext(request, {'errorMessage' : errorMessage,
                                     'const' : const,
				     'user' : request.user})
        return render_to_response('admin/change_password_fail.html', c)
    
def download(request):
    reqLogger.info("download")
    reqLogger.debug(str(request))

    currentFolder = request.GET['currentFolder']
    currentPath = request.GET['currentPath']
    fileName = request.GET['fileName']
    folder = Folder.objects.filter(name=currentFolder)[0]
    
    filePath = folder.localPath + currentPath + '/' + fileName
    
    return sendfile(request, filePath, attachment=True)

def downloadZip(request):    
    reqLogger.info("downloadZip")
    reqLogger.debug(str(request))
    return handleDownloadZip(request)

def upload(request):
    reqLogger.info("upload")
    reqLogger.debug(str(request))
    currentFolder = request.REQUEST['currentFolder']
    currentPath = request.REQUEST['currentPath']
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanWrite = folder.userCanWrite(request.user)
    
    if not userCanWrite:
        return HttpResponse("You don't have write permission on this folder")
    
    if request.REQUEST.has_key('action'):
        action = request.REQUEST['action']
        if action == 'uploadFile':
#            return HttpResponse(str(type(request.FILES['upload1'])))
            handleFileUpload(request.FILES['upload1'], folder, currentPath)
            redirectUrl = const.CONTENT_URL + "?currentFolder=" + currentFolder + "&currentPath=" + currentPath + "&status=" + 'File uploaded'
            return redirect(redirectUrl)           
        elif action == 'uploadZip':
            handleZipUpload(request.FILES['zipupload1'], folder, currentPath)
            redirectUrl = const.CONTENT_URL + "?currentFolder=" + currentFolder + "&currentPath=" + currentPath + "&status=" + 'File uploaded and extracted'
            return redirect(redirectUrl)         
    
    c = RequestContext(request,
        {'currentFolder' : currentFolder,
         'currentPath' : currentPath,
         'status' : '',
         'viewTypes' : const.viewTypes,
         'const' : const,
         'user' : request.user,
         })
    
    return render_to_response('upload.html', c)

def imageView(request):
    reqLogger.info("imageView")
    reqLogger.debug(str(request))

    currentFolder = request.REQUEST['currentFolder']
    currentPath = request.REQUEST['currentPath']
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanRead = folder.userCanRead(request.user)
    
    if not userCanRead:
        return HttpResponse("You don't have read permission on this folder")
    
    fileName = request.REQUEST['fileName']
    
    currentDirEntries = getCurrentDirEntries(folder, currentPath)
    
    for i in range(len(currentDirEntries)):
        if currentDirEntries[i].name == fileName:
            index = i
            break
        
    if i == 0:
        prevLink = None
    else:
        prevLink = const.IMAGE_VIEW_URL + "?currentFolder=" + currentFolder + "&currentPath=" + currentPath + "&fileName=" + currentDirEntries[i-1].name
        
    if i == len(currentDirEntries) - 1:
        nextLink = None
    else:
        nextLink = const.IMAGE_VIEW_URL + "?currentFolder=" + currentFolder + "&currentPath=" + currentPath + "&fileName=" + currentDirEntries[i+1].name
        
    parentDirLink = const.CONTENT_URL + "?currentFolder=" + currentFolder + "&currentPath=" + currentPath
    
    imageUrl = const.BASE_URL + '__' + currentFolder + '__' + currentPath + '/' + fileName
    imageUrl = imageUrl.replace('//','/')
    
    c = RequestContext(request,
        {'currentFolder' : currentFolder,
         'currentPath' : currentPath,
         'status' : '',
         'viewTypes' : const.viewTypes,
         'const' : const,
         'user' : request.user,
         'fileName' : fileName,
         'parentDirLink' : parentDirLink,
         'prevLink' : prevLink,
         'nextLink' : nextLink,
         'imageUrl' : imageUrl,
         })
    
    return render_to_response('image_view.html', c)
        
def thumb(request):
    reqLogger.info("thumb")
    reqLogger.debug(str(request))
    
    return render_to_response('test_image.html')
