from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from html_browser.models import Folder
from django.contrib.auth import login as auth_login, logout as auth_logout
from utils import getParentDirLink
from html_browser.utils import getCurrentDirEntries, Clipboard, handlePaste, handleDelete
from constants import _constants as const
from django.contrib.auth import authenticate
from sendfile import sendfile

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
    user = request.user
    if user == None or user.is_authenticated() == False:
        return redirect(const.BASE_URL, 'You are not authorized to view this page')
    
    currentFolder = request.REQUEST['currentFolder']
    currentPath = request.REQUEST['currentPath']        
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanDelete = folder.userCanDelete(request.user)
    userCanWrite = userCanDelete or folder.userCanWrite(request.user)
    userCanRead = userCanWrite or folder.userCanRead(request.user)    
    
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
    
    c = RequestContext(request,
        {'currentFolder' : currentFolder,
         'currentPath' : currentPath,
         'userCanRead' : str(userCanRead).lower(),
         'userCanWrite' : str(userCanWrite).lower(),
         'userCanDelete' : str(userCanDelete).lower(),
         'parentDirLink' : parentDirLink,
         'status' : status,
         'viewTypes' : const.viewTypes,
         'currentDirEntries' : currentDirEntries,
         'const' : const,
         'user' : request.user,
         })
    
    return render_to_response('content_detail.html', c)

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
    
    filePath = folder.localPath + currentPath + fileName
    
    f = open('/tmp/log.txt', 'w')
    f.write(filePath + '\n')
    f.close()
    
    return sendfile(request, filePath, attachment=True)
    
#def admin(request):
#    c = RequestContext(request,
#        {'const' : const,
#         'user' : request.user,
#         })
#    
#    return render_to_response('admin/admin.html', c)
#    
#def userAdmin(request, errorText=None):
##    debugFile.write('Inside addUserAdmin\n')
##    debugFile.flush()
#    user = request.user
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')
#    
#    users = User.objects.all()
#    groupNames = getGroupNamesForUser(user)        
#    
#    c = RequestContext(request, {'const' : const,
#         'users' : users,
#         'groupNames' : groupNames,
#         'user' : user,
#         'errorText' : errorText,
#          })
#    return render_to_response('admin/user_admin.html', c)
#         
#def addUser(request):
##    debugFile.write('Inside addUser\n')
##    debugFile.flush()
#    user = request.user
#    
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')
#        
#    groupNames = getGroupNames()    
#        
#    c = RequestContext(request,
#        {'const' : const,
#         'groupNames' : groupNames,
#         'user' : user })
#    return render_to_response('admin/add_user.html', c)        
#    
#def addUserAction(request):
##    debugFile.write('Inside addUserAction\n')
##    debugFile.flush()
#    user = request.user               
#    
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')
#    
#    userName = request.POST['userName']
#    password = request.POST['password']
#     
#    if 'isAdministrator' in request.POST:
#        isAdmin = request.POST['isAdministrator']
##        debugFile.write('isAdmin = ' + isAdmin + "\n")
#        isAdminBoolean = isAdmin in ['True', 'true', 'on', 'On']
#    else:
##        debugFile.write('no isAdmin param\n')
#        isAdminBoolean = False
#        
##    debugFile.flush()
#    
#    #TODO handle groups
#    
#    message = None
#    
#    tempUsers = User.objects.filter(username=userName)
#    if len(tempUsers) > 0:
#        message='The user already exists'    
#    elif not re.match('[A-Za-z]', userName):
#        message = 'User names must be alphabetic'
#    elif not len(userName) >= 6:
#        message = 'User names must be at least 6 characters'
#        
#    if message != None:
#        c = RequestContext(request, {
#         'message' : message,
#         'const' : const})    
#        return render_to_response('admin/add_user_result.html', c)        
#        
#    newUser = User()
#    newUser.username = userName
#    newUser.set_password(password)
#    newUser.is_staff = isAdminBoolean
#    #TODO handle groups
#    
#    newUser.save()
#    message = 'User ' + userName + ' added'
#    c = RequestContext(request, {
#         'message' : message,
#         'const' : const})    
#    return render_to_response('admin/add_user_result.html', c)
#
#def groupAdmin(request, errorText=None):
#    user = request.user
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')
#    
#    groupNames = getGroupNames()        
#    
#    c = RequestContext(request, {'const' : const,
#         'groupNames' : groupNames,
#         'user' : user,
#         'errorText' : errorText,
#          })
#    return render_to_response('admin/group_admin.html', c)
#
#def addGroup(request):
#    user = request.user
#    
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')        
#        
#    c = RequestContext(request,
#        {'const' : const,
#         'user' : user })
#    return render_to_response('admin/add_group.html', c)   

#def addGroupAction(request):
#    user = request.user               
#    
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')
#    
#    groupName = request.POST['groupName']         
#    
#    message = None
#    
#    tempGroups = Group.objects.filter(name=groupName)
#    if len(tempGroups) > 0:
#        message='The group already exists'    
#    elif not re.match('[A-Za-z]', groupName):
#        message = 'Group names must be alphabetic'
#        
#    if message != None:
#        c = RequestContext(request, {
#         'message' : message,
#         'const' : const})    
#        return render_to_response('admin/add_group_result.html', c)        
#        
#    newGroup = Group()
#    newGroup.name = groupName
#    
#    newGroup.save()
#    message = 'Group ' + groupName + ' added'
#    c = RequestContext(request, {
#         'message' : message,
#         'const' : const})    
#    return render_to_response('admin/add_group_result.html', c)
#
#def editGroup(request):
#    user = request.user               
#    
#    if user == None or user.is_authenticated == False or user.is_staff == False:
#        return redirect(const.BASE_URL, 'You are not authorized to view this page')
#    
#    groupName = request.GET['groupName']
#    
#    c = RequestContext(request, {
#         'groupName' : groupName,
#         'const' : const})    
#    return render_to_response('admin/edit_group.html', c)
