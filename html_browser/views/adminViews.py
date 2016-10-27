import logging
from logging import DEBUG

from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext

import html_browser
from html_browser.models import Folder, UserPermission, GroupPermission
from html_browser.utils import getReqLogger, getRequestField,\
    handleAddFolder, handleEditFolder, handleDeleteFolder,\
    handleEditGroup, handleAddGroup, handleDeleteGroup, \
    handleAddUser, handleEditUser, handleDeleteUser

from .base_view import BaseView

from html_browser.constants import _constants as const

logger = logging.getLogger(__name__)

class FolderViewOption():
    def __init__(self, value, display):
        self.value = value
        self.display = display

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.__str__()

folderViewOptions = []

for choice in html_browser.models.viewableChoices:
    option = FolderViewOption(choice[0], choice[1]) 
    folderViewOptions.append(option)

class AdminView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
        c = self.buildBaseContext(request)
        return render(request, 'admin/admin.html', c)

class FolderAdminActionView(BaseView):
    def post(self, request, *args, **kwargs):
        self.logGet(request)
        errorText = None

        action = getRequestField(request,'action')
        if action == 'deleteFolder':
        # there is no submit button for deleting folders as the request
        # comes from javascript
            handleDeleteFolder(request)
        elif getRequestField(request,'submit') == "Save":
            if action == 'addFolder':
                errorText = handleAddFolder(request)
            elif action == 'editFolder':
                handleEditFolder(request)
            else:
                raise RuntimeError('Unknown action %s' % action)

        redirectUrl = const.BASE_URL + "folderAdmin/" 
        if errorText != None:
            redirectUrl = redirectUrl + "?errorText=%s" % errorText

        return redirect(redirectUrl)

class FolderAdminView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)

        c = self.buildBaseContext(request)
        c['folders'] = Folder.objects.all()
        return render(request, 'admin/folder_admin.html', c)

class AddFolderView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
        c = self.buildBaseContext(request)
        #c.update({'viewOptions': folderViewOptions})
        c['viewOptions'] = folderViewOptions
        c['usersNotAssignedToFolder'] = User.objects.all()
        c['groupsNotAssignedToFolder'] = Group.objects.all()
        return render(request, 'admin/add_folder.html', c)

class EditFolderView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)

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

        c = self.buildBaseContext(request)
        c['folder'] = folder
        c['usersNotAssignedToFolder'] = usersNotInFolder
        c['groupsNotAssignedToFolder'] = groupsNotInFolder
        c['groupPermissions'] = groupPerms
        c['userPermissions'] = userPerms
        c['viewOptions'] = folderViewOptions
        return render(request, 'admin/edit_folder.html', c)

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
