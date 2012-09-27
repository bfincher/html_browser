from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from html_browser.models import Folder
from django.contrib.auth import login as auth_login, logout as auth_logout
from utils import getParentDirLink
from html_browser.utils import getCurrentDirEntries, Clipboard, handlePaste, handleDelete,\
    getPath, handleRename, handleDownloadZip, deleteOldFiles,\
    handleFileUpload, handleZipUpload
from constants import _constants as const
from django.contrib.auth import authenticate
from sendfile import sendfile
import os
from django.http import HttpResponse

def index(request, errorText=None):
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


def hbLogout(request):
    auth_logout(request)
    return redirect(const.BASE_URL)

def content(request):    
    deleteOldFiles()
    
    currentFolder = request.REQUEST['currentFolder']
    currentPath = request.REQUEST['currentPath']        
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    userCanWrite = userCanDelete or folder.userCanWrite(request.user)
    userCanRead = userCanWrite or folder.userCanRead(request.user)    
    
    if userCanRead == False:
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
    
    currentDirEntries = getCurrentDirEntries(folder, currentPath)
    
    if request.REQUEST.has_key('status'):
        status = request.REQUEST['status']
    else:
        status = ''
        
    if request.session.has_key('viewType'):
        viewType = request.session['viewType']
    else:
        viewType = const.viewTypes[0]                   
    
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
         })
    
    if viewType == const.detailsViewType:
        template = 'content_detail.html'
    elif viewType == const.listViewType:
        template = 'content_list.html'
    else:
        template = 'content_thumbnail.html'
    return render_to_response(template, c)

def hbChangePassword(request):
    c = RequestContext(request, {'const' : const})
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
        c = RequestContext(request, {'const' : const})
        return render_to_response('registration/change_password_success.html', c)
    else:
        c = RequestContext(request, {'errorMessage' : errorMessage,
                                     'const' : const})
        return render_to_response('registration/change_password_fail.html', c)
    
def download(request):
    currentFolder = request.GET['currentFolder']
    currentPath = request.GET['currentPath']
    fileName = request.GET['fileName']
    folder = Folder.objects.filter(name=currentFolder)[0]
    
    filePath = folder.localPath + currentPath + '/' + fileName
    
    return sendfile(request, filePath, attachment=True)

def downloadZip(request):    
    return handleDownloadZip(request)

def upload(request):
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
    return render_to_response('test_image.html')
