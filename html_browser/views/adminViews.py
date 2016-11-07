from abc import ABCMeta, abstractmethod
from datetime import datetime
import logging
from logging import DEBUG

from django.contrib.auth.models import User, Group
from django.db import transaction
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from annoying.functions import get_object_or_None

import html_browser
from html_browser.models import Folder, UserPermission, GroupPermission,\
CAN_READ, CAN_WRITE, CAN_DELETE
from html_browser.utils import getReqLogger
from .adminForms import AddUserForm, EditUserForm, EditGroupForm,\
UserPermissionFormSet, GroupPermissionFormSet, EditFolderForm, AddFolderForm

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
        super(AdminView, self).get(request, *args, **kwargs)
        return render(request, 'admin/admin.html', self.context)

class FolderAdminView(BaseView):
    def get(self, request, *args, **kwargs):
        super(FolderAdminView, self).get(request, *args, **kwargs)

        self.context['folders'] = Folder.objects.all()
        return render(request, 'admin/folder_admin.html', self.context)

class DeleteFolderView(BaseView):
    def post(self, request, *args, **kwargs):
        super(DeleteFolderView, self).post(request, *args, **kwargs)
        Folder.objects.filter(name=request.POST['name']).delete()
        redirectUrl = const.BASE_URL + "folderAdmin/" 
        return redirect(redirectUrl)

class AbstractFolderView(BaseView):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(AbstractFolderView, self).__init__(*args, **kwargs)
        self.folder=None
        self.folderForm=None
        self.userPermFormset=None
        self.groupPermFormset=None

    @abstractmethod
    def initForms(self, request): pass

    @abstractmethod
    def getTemplate(self): pass

    def post(self, request, *args, **kwargs):
        super(AbstractFolderView, self).post(request, *args, **kwargs)
        self.initForms(request)

        reqLogger = getReqLogger()
        if not self.folderForm.is_valid():
            reqLogger.error('folderFormErrors = %s', self.folderForm.errors)
            return self.render(request)
        elif not self.userPermFormset.is_valid():
            reqLogger.error('userPermFormset.errors = %s', self.userPermFormset.errors)
            return self.render(request)
        elif not self.groupPermFormset.is_valid():
            reqLogger.error('groupPermFormset.errors = %s', self.groupPermFormset.errors)
            return self.render(request)

        with transaction.atomic():
            folder = self.folderForm.save()

            for form in self.userPermFormset:
                if form.is_valid():
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.delete()
                    else:
                        instance = form.save(commit=False)
                        instance.folder = folder
                        instance.save()

            for form in self.groupPermFormset:
                if form.is_valid():
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.delete()
                    else:
                        instance = form.save(commit=False)
                        instance.folder = folder
                        instance.save()

        redirectUrl = const.BASE_URL + "folderAdmin/" 
        return redirect(redirectUrl)

    def get(self, request, *args, **kwargs):
        super(AbstractFolderView, self).get(request, *args, **kwargs)
        self.initForms(request)
        return self.render(request)

    def render(self, request):
        self.appendFormErrors(self.folderForm)
        self.appendFormErrors(self.userPermFormset)
        self.appendFormErrors(self.groupPermFormset)

        self.context['folder'] = self.folder
        self.context['form'] = self.folderForm
        self.context['userPermFormset'] = self.userPermFormset
        self.context['groupPermFormset'] = self.groupPermFormset

        return render(request, self.getTemplate(), self.context)

class EditFolderView(AbstractFolderView):
    def __init__(self, *args, **kwargs):
        super(EditFolderView, self).__init__(*args, **kwargs)

    def getTemplate(self):
        return 'admin/edit_folder.html'

    def initForms(self, request):
        if request.method == "GET":
            folderName = request.GET['name']
            self.folder = Folder.objects.get(name = folderName)

            self.folderForm = EditFolderForm(instance=self.folder)
            self.userPermFormset = UserPermissionFormSet(instance=self.folder)
            self.groupPermFormset = GroupPermissionFormSet(instance=self.folder)
        else:
            self.folder = Folder.objects.get(pk=request.POST['folderPk'])
            self.folderForm = EditFolderForm(request.POST, instance=self.folder)
            self.userPermFormset = UserPermissionFormSet(request.POST, instance=self.folder)
            self.groupPermFormset = GroupPermissionFormSet(request.POST, instance=self.folder)

class AddFolderView(AbstractFolderView):
    def __init__(self, *args, **kwargs):
        super(AddFolderView, self).__init__(*args, **kwargs)

    def getTemplate(self):
        return 'admin/add_folder.html'

    def initForms(self, request):
        if request.method == "GET":
            self.folder = Folder()
            self.folderForm = AddFolderForm(instance=self.folder)
            self.userPermFormset = UserPermissionFormSet(instance=self.folder)
            self.groupPermFormset = GroupPermissionFormSet(instance=self.folder)
        else:
            self.folderForm = AddFolderForm(request.POST)
            self.userPermFormset = UserPermissionFormSet(request.POST)
            self.groupPermFormset = GroupPermissionFormSet(request.POST)

class AddGroupView(BaseView):
    def post(self, request, *args, **kwargs):
        super(AddGroupView, self).post(request, *args, **kwargs)
        redirectUrl = const.BASE_URL + "groupAdmin/"
        groupName = request.POST['groupName']
        group = get_object_or_None(Group, name=groupName)
        if not group:
            group = Group()
            group.name = groupName
            group.save()
        else:
            redirectUrl = redirectUrl + "?errorText=Group %s already exists" % groupName

        return redirect(redirectUrl)

class DeleteGroupView(BaseView):
    def post(self, request, *args, **kwargs):
        super(DeleteGroupView, self).__init__(*args, **kwargs)
        groupName = request.POST['groupToDelete']
        group = Group.objects.get(name=groupName)
        group.delete()

        redirectUrl = const.BASE_URL + "groupAdmin/"
        return redirect(redirectUrl)

class AddGroupActionView(BaseView):
    def post(self, request, *args, **kwargs):
        super(AddGroupActionView, self).__init__(*args, **kwargs)
        errorText = None
        groupName = request.POST['groupName']
        group = get_object_or_None(Group, name=groupName)
        if not group:
            group = Group()
            group.name = groupName
            group.save()
        else:
            errorText = "Group %s already exists" % groupName

        redirectUrl = const.BASE_URL + "groupAdmin/"
        if errorText != None:
            redirectUrl = redirectUrl + "?errorText=%s" % errorText

        return redirect(redirectUrl)           

class EditGroupActionView(BaseView):
    def post(self, request, *args, **kwargs):
        super(EditGroupActionView, self).__init__(*args, **kwargs)
        form = EditGroupForm(request.POST)
        if form.is_valid():
            group = Group.objects.get(name=form.cleaned_data['groupName'])
            group.user_set.clear()

            for userName in form.cleaned_data['users']:
                user = User.objects.get(username=userName)
                group.user_set.add(user)
            group.save()
        else:
            reqLogger = getReqLogger()
            reqLogger.error('form.errors = %s', form.errors)

        redirectUrl = const.BASE_URL + "groupAdmin/"
        return redirect(redirectUrl)           

class EditGroupView(BaseView):
    def get(self, request, *args, **kwargs):
        super(EditGroupView, self).get(request, *args, **kwargs)
        groupName = request.GET['groupName']
        group = Group.objects.get(name = groupName)

        form = EditGroupForm()
        form.setGroup(group)

        self.context['groupName'] = groupName
        self.context['form'] = form
        return render(request, 'admin/edit_group.html', self.context)

class GroupAdminView(BaseView):
    def get(self, request, *args, **kwargs):
        super(GroupAdminView, self).get(request, *args, **kwargs)
        groups = []
        for group in Group.objects.all():
            groups.append(group.name)

        self.context['groups'] = groups
        return render(request, 'admin/group_admin.html', self.context)

class DeleteUserView(BaseView):
    def post(self, request, *args, **kwargs):
        super(DeleteUserView, self).post(request, *args, **kwargs)
        redirectUrl = const.BASE_URL + "userAdmin/"

        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        if request.user.username == request.POST['userToDelete']:
            redirectUrl += "?errorText=Unable to delete current user"
            return redirect(redirectUrl)           
            
        user = User.objects.get(username=request.POST['userToDelete'])
        logger.info("Deleting user %s", user)
        user.delete()

        return redirect(redirectUrl)           

class UserAdminView(BaseView):
    def get(self, request, *args, **kwargs):
        super(UserAdminView, self).get(request, *args, **kwargs)

        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        self.context['users'] = User.objects.all()
        return render(request, 'admin/user_admin.html', self.context)

class AbstractUserView(BaseView):
    __metaclass__ = ABCMeta

    @abstractmethod
    def initForm(self, request): pass

    @abstractmethod
    def getTemplate(self): pass

    def get(self, request, *args, **kwargs):
        super(AbstractUserView, self).get(request, *args, **kwargs)
        if not request.user.is_staff:
            raise RuntimeError("User is not an admin")

        self.initForm(request)

        if self.form.instance:
            self.context['username'] = self.form.instance.username
        self.context['form'] = self.form
        return render(request, self.getTemplate(), self.context)

    def post(self, request, *args, **kwargs):
        super(AbstractUserView, self).post(request, *args, **kwargs)
        errorText = None

        self.initForm(request)

        if self.form.is_valid():
            user = self.form.save()

            user.groups.clear()
            for group in self.form.cleaned_data['groups']:
                user.groups.add(group)

            user.is_staff = user.is_superuser
            if not user.last_login:
                user.last_login = datetime(year=1970, month=1, day=1)
            user.save()
        else:
            reqLogger = getReqLogger()
            reqLogger.error('form.errors = %s', form.errors)

        redirectUrl = const.BASE_URL + "userAdmin/"
        if errorText != None:
            redirectUrl = redirectUrl + "?errorText=%s" % errorText

        return redirect(redirectUrl)           
    
class EditUserView(AbstractUserView):
    def initForm(self, request):
        if request.method == "GET":
            userName = request.GET['userName']
            user = User.objects.get(username=userName)
            self.form = EditUserForm(instance=user)
        else:
            user = User.objects.get(pk=request.POST['userPk'])
            self.form = EditUserForm(request.POST, instance=user)

    def getTemplate(self):
        return 'admin/edit_user.html'

class AddUserView(AbstractUserView):
    def initForm(self, request):
        if request.method == "GET":
            self.form = AddUserForm()
        else:
            self.form = AddUserForm(request.POST)

    def getTemplate(self):
        return 'admin/add_user.html'

class ChangePasswordView(BaseView):
    def get(self, request, *args, **kwargs):
        super(ChangePasswordView, self).get(request, *args, **kwargs)
        return render(request, 'admin/change_password.html', self.context)

class ChangePasswordResultView(BaseView):
    def get(self, request, *args, **kwargs):
        super(ChangePasswordView, self).get(request, *args, **kwargs)
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
            return render(request, 'admin/change_password_success.html', self.context)
        else:
            reqLogger.warn(errorMessage)
            self.context['errorMessage'] = errorMessage
            return render(request, 'admin/change_password_fail.html', self.context)
