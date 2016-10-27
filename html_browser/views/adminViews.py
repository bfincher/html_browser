from datetime import datetime
import logging
from logging import DEBUG

from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from annoying.functions import get_object_or_None

import html_browser
from html_browser.models import Folder, UserPermission, GroupPermission,\
CAN_READ, CAN_WRITE, CAN_DELETE
from html_browser.utils import getReqLogger

from .base_view import BaseView

from html_browser.constants import _constants as const

_permMap = {'read' : CAN_READ, 'write' : CAN_WRITE, 'delete' : CAN_DELETE}
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

        action = request.POST['action']
        if action == 'deleteFolder':
        # there is no submit button for deleting folders as the request
        # comes from javascript
            folderName = request.POST['name']
            folder = Folder.objects.get(name=folderName)
            folder.delete()
        elif request.POST['submit'] == "Save":
            if action == 'addFolder':
                folderName = request.POST['name']
                folder = Folder()
                folder.name = folderName
                handleEditFolder(request, folder)
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

        folderName = request.GET['name']
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

class GroupAdminActionView(BaseView):
    def post(self, request, *args, **kwargs):
        self.logGet(request)

        errorText = None

        action = request.POST['action']
        if action == 'deleteGroup':
            groupName = request.POST['groupToDelete']
            group = Group.objects.get(name=groupName)
            group.delete()
        elif action == 'addGroup':
            groupName = request.POST['groupName']
            group = get_object_or_None(Group, name=groupName)
            if not group:
                group = Group()
                group.name = groupName
                group.save()
            else:
                errorText = "Group %s already exists" % groupName
        elif request.POST['submit'] == "Save":
            if action == 'editGroup':
                group = Group.objects.get(name=request.POST['groupName'])
                group.user_set.clear()

                for key in REQUEST.POST:
                    if key.startswith("isUser"):
                        if logger.isEnabledFor(DEBUG):
                            logger.debug("processing key $s", key)
                        userName = key[6:]
                        user = User.objects.get(username=userName)
                        group.user_set.add(user)
            else:
                raise RuntimeError('Unknown action %s' % action)

        redirectUrl = const.BASE_URL + "groupAdmin/"
        if errorText != None:
            redirectUrl = redirectUrl + "?errorText=%s" % errorText

        return redirect(redirectUrl)           

class EditGroupView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
        groupName = request.GET['groupName']
        group = Group.objects.get(name = groupName)

        usersInGroup = User.objects.filter(groups__id=group.id)
        otherUsers = User.objects.exclude(groups__id=group.id)

        activeUserNames = []
        for user in usersInGroup:
            activeUserNames.append(user.username)

        userNames = []
        for user in otherUsers:
            userNames.append(user.username)

        c = self.buildBaseContext(request)
        c['groupName'] = groupName
        c['activeUserNames'] = activeUserNames
        c['userNames'] = userNames
        return render(request, 'admin/edit_group.html', c)

class GroupAdminView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
        groups = []
        for group in Group.objects.all():
            groups.append(group.name)

        c = self.buildBaseContext(request)
        c['groups'] = groups
        return render(request, 'admin/group_admin.html', c)

class UserAdminActionView(BaseView):
    def post(self, request, *args, **kwargs):
        self.logGet(request)
        errorText = None

        action = request.POST['action']
        if action == 'deleteUser':
            if not request.user.is_staff:
                raise RuntimeError("User is not an admin")
            user = User.objects.get(username=request.POST['userToDelete'])
            logger.info("Deleting user %s", user)
            user.delete()
        elif request.POST['submit'] == "Save":
            if not request.user.is_staff:
                raise RuntimeError("User is not an admin")

            if action == 'editUser':
                userName = request.POST['userName']

                password = None
                if 'password' in request.POST:
                    password = request.POST['password']

                isAdmin = 'isAdministrator' in request.POST

                user = User.objects.get(username=userName)
                if password:
                    user.set_password(password)
                user.is_staff = isAdmin
                user.is_superuser = isAdmin
                user.is_active = True
                user.save()

                assignGroupsToUser(user, request.POST)
                #userGroups = user.groups.all()

                user.save()
            elif action == 'addUser':
                userName = request.POST['userName']

                user = get_object_or_None(User, username=userName)
                if user:
                    errorText = "User %s already exists" % userName

                password = request.POST['password']

                isAdmin = request.POST.has_key('isAdministrator')

                user = User()
                user.username = userName;
                user.set_password(password)
                user.is_staff = isAdmin
                user.is_superuser = isAdmin
                user.is_active = True
                user.last_login = datetime(year=1970, month=1, day=1)
                user.save()
                assignGroupsToUser(user, request)
                user.save()
            else:
                raise RuntimeError('Unknown action %s' % action)

        redirectUrl = const.BASE_URL + "userAdmin/"
        if errorText != None:
            redirectUrl = redirectUrl + "?errorText=%s" % errorText

        return redirect(redirectUrl)           

class UserAdminView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)

        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        c = self.buildBaseContext(request)
        c['users'] = User.objects.all()
        return render(request, 'admin/user_admin.html', c)

class EditUserView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        userName = request.GET['userName']
        reqLogger = getReqLogger()
        reqLogger.info("editUser: user = %s", userName)

        editUser = User.objects.get(username=userName)

        activeGroupNames = []
        groupNames = []

        for group in editUser.groups.all():
            activeGroupNames.append(group.name)

        for group in Group.objects.exclude(id__in = editUser.groups.all().values_list('id', flat=True)):
            groupNames.append(group.name)

        c = self.buildBaseContext(request)
        c['editUser'] = editUser
        c['activeGroupNames'] = activeGroupNames
        c['groupNames'] = groupNames
        return render(request, 'admin/edit_user.html', c)

class AddUserView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)

        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        groupNames = []

        for group in Group.objects.all():
            groupNames.append(group.name)

        c = self.buildBaseContext(request)
        c['groupNames'] = groupNames

        return render(request, 'admin/add_user.html', c)

class ChangePasswordView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
        c = self.buildBaseContext(request)
        return render(request, 'admin/change_password.html', c)

class ChangePasswordResultView(BaseView):
    def get(self, request, *args, **kwargs):
        self.logGet(request)
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
        
        context = self.buildBaseContext(request)
        if errorMessage == None:
            return render_to_response(request, 'admin/change_password_success.html', context)
        else:
            reqLogger.warn(errorMessage)
            context['errorMessage'] = errorMessage
            return render_to_response(request, 'admin/change_password_fail.html', context)

def handleEditFolder(request, folder=None):
    if folder == None:
        folderName = request.POST['name']
        folder = Folder.objects.get(name=folderName)

    folder.localPath = request.POST['directory']
    folder.viewOption = request.POST['viewOption']
    folder.save()

    newUsers = {}
    newGroups = {}
    for key in request.POST:
        if key.startswith('user-'):
            tokens = key.split('-')
            newUsers[tokens[1]] = tokens[2]
        elif key.startswith('group-'):
            tokens = key.split('-')
            newGroups[tokens[1]] = tokens[2]

    for userPerm in UserPermission.objects.filter(folder = folder):
        if newUsers.has_key(userPerm.user.username):
            userPerm.permission = _permMap[newUsers[userPerm.user.username]]
            userPerm.save()

            del newUsers[userPerm.user.username]

        else:
            userPerm.delete()

    for key in newUsers:
        perm = UserPermission()
        perm.folder = folder
        perm.permission = _permMap[newUsers[key]]
        perm.user = User.objects.get(username = key)
        perm.save()
    
    for groupPerm in GroupPermission.objects.filter(folder = folder):
        if newGroups.has_key(groupPerm.group.name):
            groupPerm.permission = _permMap[newGroups[groupPerm.group.name]]
            groupPerm.save()

            del newGroups[groupPerm.group.name]

        else:
            groupPerm.delete()

    for key in newGroups:
        perm = GroupPermission()
        perm.folder = folder
        perm.permission = _permMap[newGroups[key]]
        perm.group = Group.objects.get(name = key)
        perm.save()


def assignGroupsToUser(user,requestDict):
    user.groups.clear()

    for key in requestDict:
        if key.startswith("isGroup"):
            groupName = key[7:]
            if logger.isEnabledFor(DEBUG):
                logger.debug("processing key %s", key)
                logger.debug("groupName = %s", groupName)
            group = Group.objects.get(name=groupName)
            user.groups.add(group)
