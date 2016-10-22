from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from html_browser.models import Folder, UserPermission, GroupPermission
from django.contrib.auth import login as auth_login, logout as auth_logout
from utils import getParentDirLink
import html_browser
from html_browser.utils import getCurrentDirEntries, getCurrentDirEntriesSearch, Clipboard, handlePaste, handleDelete,\
    getPath, handleRename, handleDownloadZip, deleteOldFiles,\
    handleFileUpload, handleZipUpload, getDiskPercentFree,\
    getDiskUsageFormatted, handleAddUser, handleEditUser, handleDeleteUser,\
    handleAddGroup, handleEditGroup, handleDeleteGroup, \
    handleEditFolder, handleAddFolder, handleDeleteFolder, \
    getRequestField
from constants import _constants as const
from django.contrib.auth import authenticate
from sendfile import sendfile
import os
import re
import json
from django.http import HttpResponse
import logging
from logging import DEBUG
from django.contrib.auth.models import User, Group
import HTMLParser

logger = logging.getLogger(__name__)
_reqLogger = None
imageRegex = re.compile("^([a-z])+.*\.(jpg|png|gif|bmp|avi)$",re.IGNORECASE)

class FolderViewOption():
    def __init__(self, value, display):
        self.value = value
        self.display = display

folderViewOptions = []

for choice in html_browser.models.viewableChoices:
    option = FolderViewOption(choice[0], choice[1]) 
    folderViewOptions.append(option)

def getReqLogger():
    if not _reqLogger:
        global _reqLogger
        _reqLogger = logging.getLogger('django.request')
    return _reqLogger;

def index(request):
    reqLogger = getReqLogger()
    reqLogger.info('index ')
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug(str(request))

    errorText = getRequestField(request, 'errorText')

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

    reqLogger = getReqLogger()
    reqLogger.info("hbLogin")
    if userName is not None:
        reqLogger.info("userName = %s" % userName)
    
    errorText = None
    
    user = authenticate(username=userName, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            if reqLogger.isEnabledFor(DEBUG):
                reqLogger.debug("%s authenticated", user)
        else:
            reqLogger.warn("%s attempted to log in to a disabled account", user)
            errorText = 'Account has been disabled'
    else:
        errorText = 'Invalid login'
        reqLogger.error("empty userName")
    
    redirectUrl = const.BASE_URL

    if errorText != None:
        redirectUrl = "%s?errorText=%s" % (redirectUrl, errorText)
    return redirect(redirectUrl)


def hbLogout(request):
    reqLogger = getReqLogger()
    reqLogger.info("user %s logged out", request.user)
    auth_logout(request)
    return redirect(const.BASE_URL)

def content(request):    
    reqLogger = getReqLogger()
    reqLogger.info("content")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)
    deleteOldFiles()
    
    currentFolder = getRequestField(request,'currentFolder')
    h = HTMLParser.HTMLParser()
    currentPath = h.unescape(getRequestField(request,'currentPath'))
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    userCanWrite = userCanDelete or folder.userCanWrite(request.user)
    userCanRead = userCanWrite or folder.userCanRead(request.user)    
    
    if userCanRead == False:
        reqLogger.warn("%s not allowed to read %s", request.user, currentFolder)
        return redirect(const.BASE_URL, 'You are not authorized to view this page')
    
    status = ''
    statusError = None

    action = getRequestField(request,'action')
    if action:
        if action == 'copyToClipboard':
            entries = getRequestField(request,'entries')
            request.session['clipboard'] = Clipboard(currentFolder, currentPath, entries, 'COPY').toJson()
            status='Items copied to clipboard';
        elif action == 'cutToClipboard':
            if not userCanDelete:
                status="You don't have delete permission on this folder"
                statusError = True
            else:
                entries = getRequestField(request,'entries')
                request.session['clipboard'] = Clipboard(currentFolder, currentPath, entries, 'CUT').toJson()
                status = 'Items copied to clipboard'
        elif action == 'pasteFromClipboard':
            if not userCanWrite:
                status = "You don't have write permission on this folder"
                statusError = True
            else:
                status = handlePaste(currentFolder, currentPath, Clipboard.fromJson(request.session['clipboard']))
                if status:
                    statusError = True
                else:
                    status = 'Items pasted'
        elif action == 'deleteEntry':
            if not userCanDelete:
                status = "You don't have delete permission on this folder"
                statusError = True
            else:
                handleDelete(folder, currentPath, getRequestField(request,'entries'))
                status = 'File(s) deleted'
        elif action=='setViewType':
            viewType = getRequestField(request,'viewType')
            request.session['viewType'] = viewType
        elif action == 'mkDir':
            dirName = getRequestField(request,'dir')
            os.makedirs(getPath(folder.localPath, currentPath) + dirName)
        elif action == 'rename':
            handleRename(folder, currentPath, getRequestField(request,'file'), getRequestField(request,'newName'))
        elif action == 'changeSettings':
            if getRequestField(request,'submit') == "Save":
                request.session['showHidden'] = getRequestField(request,'showHidden') != None
        else:
            raise RuntimeError('Unknown action %s' % action)
        
        redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=%s" % (const.CONTENT_URL, currentFolder, currentPath, status)

        if statusError:
            redirectUrl += "&statusError=%s" % statusError

        return redirect(redirectUrl)        
    
    parentDirLink = getParentDirLink(currentPath, currentFolder)
    
    status = getRequestField(request,'status', '')

    statusError = getRequestField(request,'statusError')

    breadcrumbs = None
    crumbs = currentPath.split("/")
    if len(crumbs) > 1:
        breadcrumbs = "<a href=\"%s\">Home</a> " % const.BASE_URL
        breadcrumbs = breadcrumbs + "&rsaquo; <a href=\"%scontent/?currentFolder=%s&currentPath=\">%s</a> " % (const.BASE_URL, currentFolder, currentFolder)
        crumbs = currentPath.split("/")
        accumulated = ""
        while len(crumbs) > 0:
            crumb = crumbs.pop(0)
            if crumb:
                accumulated = "/".join([accumulated, crumb])
                breadcrumbs = breadcrumbs + "&rsaquo; "
                if len(crumbs) > 0:
                    breadcrumbs = breadcrumbs + "<a href=\"%scontent/?currentFolder=%s&currentPath=%s\">%s</a> " % (const.BASE_URL, currentFolder, accumulated, crumb)
                else:
                    breadcrumbs = breadcrumbs + crumb

    contentFilter = getRequestField(request,'filter')
    if contentFilter:
        status = status + ' Filtered on %s' % getRequestField(request,'filter')

    search = getRequestField(request,'search')
    if search:
        currentDirEntries= getCurrentDirEntriesSearch(folder, currentPath, __isShowHidden(request), search)

        values = {'currentFolder' : currentFolder,
             'currentPath' : currentPath,
             'userCanRead' : str(userCanRead).lower(),
             'userCanWrite' : str(userCanWrite).lower(),
             'userCanDelete' : str(userCanDelete).lower(),
             'status' : status,
             'currentDirEntries' : currentDirEntries,
             'const' : const,
             'user' : request.user,
             'breadcrumbs' : breadcrumbs,
             'showHidden' : __isShowHidden(request),
        }
        if statusError:
            values['statusError'] = True
        c = RequestContext(request, values)
        return render_to_response("content_search.html", c)

    currentDirEntries = getCurrentDirEntries(folder, currentPath, __isShowHidden(request), contentFilter)
    
    if request.session.has_key('viewType'):
        viewType = request.session['viewType']
    else:
        viewType = const.viewTypes[0]                   

    diskFreePct = getDiskPercentFree(getPath(folder.localPath, currentPath))
    diskUsage = getDiskUsageFormatted(getPath(folder.localPath, currentPath))

    values = {'currentFolder' : currentFolder,
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
         'breadcrumbs' : breadcrumbs,
         'showHidden' : __isShowHidden(request),
    }
    if statusError:
        values['statusError'] = True
    c = RequestContext(request, values)
    
    if viewType == const.detailsViewType:
        template = 'content_detail.html'
    elif viewType == const.listViewType:
        template = 'content_list.html'
    else:
        template = 'content_thumbnail.html'
    return render_to_response(template, c)

def hbAdmin(request):
    reqLogger = getReqLogger()
    reqLogger.info("admin")

    c = RequestContext(request, 
        {'const' : const,
         'user' : request.user
        })
    return render_to_response('admin/admin.html', c)

def folderAdminAction(request):
    reqLogger = getReqLogger()
    reqLogger.info("folderAdminAction")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    errorText = None

    if getRequestField(request,'submit') == "Save":
        action = getRequestField(request,'action')
        if action == 'addFolder':
            errorText = handleAddFolder(request)
        elif action == 'editFolder':
            handleEditFolder(request)
        elif action == 'deleteFolder':
            handleDeleteFolder(request)
        else:
            raise RuntimeError('Unknown action %s' % action)

    redirectUrl = const.BASE_URL + "folderAdmin/"
    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=%s" % errorText

    return redirect(redirectUrl)           
    pass

def folderAdmin(request):
    reqLogger = getReqLogger()
    reqLogger.info("folderAdmin")

    c = RequestContext(request,
        {'const' : const,
         'folders' : Folder.objects.all(),
        })
    return render_to_response('admin/folder_admin.html', c)

def addFolder(request):
    c = RequestContext(request,
        {'const' : const,
         'viewOptions' : folderViewOptions,
         'usersNotAssignedToFolder' : User.objects.all(),
         'groupsNotAssignedToFolder' : Group.objects.all(),
        })
    return render_to_response('admin/add_folder.html', c)

def editFolder(request):
    reqLogger = getReqLogger()
    reqLogger.info("editFolder")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    folderName = getRequestField(request,'name')
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
         'viewOptions' : folderViewOptions,
        })
    return render_to_response('admin/edit_folder.html', c)

def groupAdminAction(request):
    reqLogger = getReqLogger()
    reqLogger.info("groupAdminAction")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    errorText = None

    if getRequestField(request,'submit') == "Save":
        action = getRequestField(request,'action')
        if action == 'addGroup':
            errorText = handleAddGroup(request)
        elif action == 'editGroup':
            handleEditGroup(request)
        elif action == 'deleteGroup':
            handleDeleteGroup(request)
        else:
            raise RuntimeError('Unknown action %s' % action)

    redirectUrl = const.BASE_URL + "groupAdmin/"
    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=%s" % errorText

    return redirect(redirectUrl)           

def editGroup(request):
    reqLogger = getReqLogger()
    reqLogger.info("editGroup")

    groupName = getRequestField(request,'groupName')
    group = Group.objects.get(name = groupName)

    usersInGroup = User.objects.filter(groups__id=group.id)
    otherUsers = User.objects.exclude(groups__id=group.id)

    activeUserNames = []
    for user in usersInGroup:
        activeUserNames.append(user.username)

    userNames = []
    for user in otherUsers:
        userNames.append(user.username)

    c = RequestContext(request, 
        {'const' : const,
         'groupName' : groupName,
         'activeUserNames' : activeUserNames,
         'userNames' : userNames,
        })
    return render_to_response('admin/edit_group.html', c)

def groupAdmin(request):
    reqLogger = getReqLogger()
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
    reqLogger = getReqLogger()
    reqLogger.info("userAdminAction")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)
    errorText = None

    if getRequestField(request,'submit') == "Save":
        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        action = getRequestField(request,'action')
        if action == 'editUser':
            handleEditUser(request.POST)
        elif action == 'addUser':
            errorText = handleAddUser(request.POST)
        elif action == 'deleteUser':
            handleDeleteUser(request)
        else:
            raise RuntimeError('Unknown action %s' % action)

    redirectUrl = const.BASE_URL + "userAdmin/"
    if errorText != None:
        redirectUrl = redirectUrl + "?errorText=%s" % errorText

    return redirect(redirectUrl)           

def userAdmin(request):
    reqLogger = getReqLogger()
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

    userName = getRequestField(request,'userName')
    reqLogger = getReqLogger()
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
    reqLogger = getReqLogger()
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
    reqLogger = getReqLogger()
    reqLogger.info("hbChangePassword")
    c = RequestContext(request, 
        {'const' : const,
         'user' : request.user
        })
    return render_to_response('admin/change_password.html', c)

def hbChangePasswordResult(request):
    user = request.user
    reqLogger = getReqLogger()
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
        return render_to_response('admin/change_password_success.html', c)
    else:
        reqLogger.warn(errorMessage)
        c = RequestContext(request, {'errorMessage' : errorMessage,
                                     'const' : const,
                                     'user' : request.user})
        return render_to_response('admin/change_password_fail.html', c)
    
def download(request):
    reqLogger = getReqLogger()
    reqLogger.info("download")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    currentFolder = request.GET['currentFolder']
    currentPath = request.GET['currentPath']
    fileName = request.GET['fileName']
    folder = Folder.objects.filter(name=currentFolder)[0]
    
    filePath = "/".join([folder.localPath + currentPath, fileName])
    
    return sendfile(request, filePath, attachment=True)

def downloadZip(request):    
    reqLogger = getReqLogger()
    reqLogger.info("downloadZip")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)
    return handleDownloadZip(request)

def upload(request):
    reqLogger = getReqLogger()
    reqLogger.info("upload")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)
    currentFolder = getRequestField(request,'currentFolder', getOrPost = request.GET)
    currentPath = getRequestField(request,'currentPath', getOrPost = request.GET)
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanWrite = folder.userCanWrite(request.user)
    
    if not userCanWrite:
        return HttpResponse("You don't have write permission on this folder")
    
    action = getRequestField(request,'action', getOrPost = request.GET)
    if action:
        if action == 'uploadFile':
#            return HttpResponse(str(type(request.FILES['upload1'])))
            handleFileUpload(request.FILES['upload1'], folder, currentPath)
            redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=File uploaded" % (const.CONTENT_URL, currentFolder, currentPath)
            return redirect(redirectUrl)           
        elif action == 'uploadZip':
            handleZipUpload(request.FILES['zipupload1'], folder, currentPath)
            redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=File uploaded and extracted" % (const.CONTENT_URL, currentFolder, currentPath)
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

def __isShowHidden(request):
    if request.session.has_key('showHidden'):
        return request.session['showHidden']
    else:
        return False

def __getIndexIntoCurrentDir(request, currentFolder, currentPath, fileName):
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanRead = folder.userCanRead(request.user)
    
    if not userCanRead:
        return HttpResponse("You don't have read permission on this folder")
    
    currentDirEntries = getCurrentDirEntries(folder, currentPath, __isShowHidden(request))
    
    for i in range(len(currentDirEntries)):
        if currentDirEntries[i].name == fileName:
            index = i
            result = {'currentDirEntries' : currentDirEntries,
                'index' : i}
            return result
        

def imageView(request):
    reqLogger = getReqLogger()
    reqLogger.info("imageView")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    currentFolder = getRequestField(request,'currentFolder')
    currentPath = getRequestField(request,'currentPath')
    fileName = getRequestField(request,'fileName')
    entries = __getIndexIntoCurrentDir(request, currentFolder, currentPath, fileName)
    index = entries['index']
    currentDirEntries = entries['currentDirEntries']

    if index == 0:
        prevLink = None
    else:
        prevLink = "%s?currentFolder=%s&currentPath=%s&fileName=%s" %(const.IMAGE_VIEW_URL, currentFolder, currentPath, currentDirEntries[index-1].name)
        
    if index == len(currentDirEntries) - 1:
        nextLink = None
    else:
        nextLink = "%s?currentFolder=%s&currentPath=%s&fileName=%s" %(const.IMAGE_VIEW_URL, currentFolder, currentPath, currentDirEntries[index+1].name)
        
    parentDirLink = "%s?currentFolder=%s&currentPath=%s" %(const.CONTENT_URL, currentFolder, currentPath)
    
    imageUrl = '%s__%s__%s/%s' %(const.BASE_URL, currentFolder, currentPath, fileName)
    imageUrl = imageUrl.replace('//','/')

    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    
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
         'fileName' : fileName,
         'userCanDelete' : userCanDelete,
         })
    
    return render_to_response('image_view.html', c)
        
def thumb(request):
    reqLogger = getReqLogger()
    reqLogger.info("thumb")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)
    
    return render_to_response('test_image.html')

def deleteImage(request):
    reqLogger = getReqLogger()
    reqLogger.info("deleteImage")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    currentFolder = getRequestField(request,'currentFolder')
    currentPath = getRequestField(request,'currentPath')
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    
    if not userCanDelete:
        status = "You don't have delete permission on this folder"
    else:
        handleDelete(folder, currentPath, getRequestField(request,'fileName'))
        status = "File deleted"

    redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=%s" % (const.CONTENT_URL, currentFolder, currentPath, status)

    return redirect(redirectUrl)

def getNextImage(request):
    reqLogger = getReqLogger()
    reqLogger.info("getNextImage")
    if reqLogger.isEnabledFor(DEBUG):
        reqLogger.debug("request = %s", request)

    currentFolder = getRequestField(request,'currentFolder')
    currentPath = getRequestField(request,'currentPath')
    fileName = getRequestField(request,'fileName')

    result = {}
    entries = __getIndexIntoCurrentDir(request, currentFolder, currentPath, fileName)
    if entries:
        index = entries['index']
        currentDirEntries = entries['currentDirEntries']

        result['hasNextImage'] = False

        for i in range(index+1, len(currentDirEntries)):
            if imageRegex.match(currentDirEntries[i].name):
                result['hasNextImage'] = True
                nextFileName = currentDirEntries[i].name

                imageUrl = '%s__%s__%s/%s' %(const.BASE_URL, currentFolder, currentPath, nextFileName)
                imageUrl = imageUrl.replace('//','/')
                result['imageUrl'] = imageUrl
                result['fileName'] = nextFileName
                break;

    data = json.dumps(result)
    return HttpResponse(data, content_type='application/json')
