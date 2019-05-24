from abc import ABCMeta, abstractmethod
from datetime import datetime
import logging
import os
import re

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from annoying.functions import get_object_or_None

import html_browser
from html_browser.models import Folder, CAN_READ, CAN_WRITE, CAN_DELETE
from html_browser.utils import getReqLogger, getFolderLinkDir
from .adminForms import AddUserForm, EditUserForm, EditGroupForm,\
    UserPermissionFormSet, GroupPermissionFormSet, EditFolderForm, AddFolderForm

from .base_view import BaseView

groupNameRegex = re.compile(r'^\w+$')
_permMap = {'read': CAN_READ, 'write': CAN_WRITE, 'delete': CAN_DELETE}
logger = logging.getLogger('html_browser.adminViews')


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


class BaseAdminView(UserPassesTestMixin, BaseView):
    def test_func(self):
        if not self.request.user.is_staff:
            messages.error(self.request, "User is not an admin")
            return False

        return True

    def appendFormErrors(self, form):
        if form.errors:
            for error in form.errors:
                messages.error(self.request, error)

        try:
            if form.non_form_errors:
                for error in form.non_form_errors():
                    messages.error(self.request, error)
        except AttributeError:
            pass


class AdminView(BaseAdminView):
    def get(self, request, *args, **kwargs):
        return render(request, 'admin/admin.html', self.context)


class FolderAdminView(BaseAdminView):
    def get(self, request, *args, **kwargs):
        self.context['folders'] = Folder.objects.all()
        return render(request, 'admin/folder_admin.html', self.context)


class DeleteFolderView(BaseAdminView):
    def post(self, request, folderName, *args, **kwargs):
        folder = Folder.objects.get(name=folderName)
        folderLinkDir = getFolderLinkDir(folder.name)

        try:
            os.remove(folderLinkDir)
        except FileNotFoundError as e:
            self.reqLogger.exception(e)
            
        folder.delete()
        return redirect('folderAdmin')


class AbstractFolderView(BaseAdminView, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = None
        self.folderForm = None
        self.userPermFormset = None
        self.groupPermFormset = None

    @abstractmethod
    def initForms(self, request, *args, **kwargs):
        pass

    def postSaveAction(self, folder):
        pass

    def post(self, request, *args, **kwargs):
        self.initForms(request, *args, **kwargs)

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

            self.postSaveAction(folder)

        return redirect('folderAdmin')

    def get(self, request, *args, **kwargs):
        self.initForms(request, *args, **kwargs)
        return self.render(request)

    def render(self, request):
        self.appendFormErrors(self.folderForm)
        self.appendFormErrors(self.userPermFormset)
        self.appendFormErrors(self.groupPermFormset)

        self.context['folder'] = self.folder
        self.context['form'] = self.folderForm
        self.context['userPermFormset'] = self.userPermFormset
        self.context['groupPermFormset'] = self.groupPermFormset
        self.context['title'] = self.title

        return render(request, 'admin/add_edit_folder.html', self.context)


class EditFolderView(AbstractFolderView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request, title, folderName, *args, **kwargs):
        self.title = title
        self.folderName = folderName
        return super().get(request, *args, **kwargs)

    def post(self, request, title, folderName, *args, **kwargs):
        self.title = title
        self.folderName = folderName
        self.origLocalPath = Folder.objects.get(name=folderName).localPath

        return super().post(request, *args, **kwargs)

    def postSaveAction(self, folder):
        modifiedLocalPath = folder.localPath
        if self.origLocalPath != modifiedLocalPath:
            folderLinkDir = getFolderLinkDir(folder.name)
            os.remove(folderLinkDir)
            os.symlink(modifiedLocalPath, folderLinkDir)

    def initForms(self, request, *args, **kwargs):
        self.folder = Folder.objects.get(name=self.folderName)

        if request.method == "GET":
            self.folderForm = EditFolderForm(instance=self.folder)
            self.userPermFormset = UserPermissionFormSet(instance=self.folder)
            self.groupPermFormset = GroupPermissionFormSet(instance=self.folder)
        else:
            self.folderForm = EditFolderForm(request.POST, instance=self.folder)
            self.userPermFormset = UserPermissionFormSet(request.POST, instance=self.folder)
            self.groupPermFormset = GroupPermissionFormSet(request.POST, instance=self.folder)


class AddFolderView(AbstractFolderView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request, title, *args, **kwargs):
        self.title = title
        return super().get(request, *args, **kwargs)

    def post(self, request, title, *args, **kwargs):
        self.title = title
        return super().post(request, *args, **kwargs)

    def postSaveAction(self, folder):
        folderLinkDir = getFolderLinkDir(folder.name)
        if os.path.exists(folderLinkDir):
            os.remove(folderLinkDir)

        os.symlink(folder.localPath, folderLinkDir)

    def initForms(self, request, *args, **kwargs):
        if request.method == "GET":
            self.folder = Folder()
            self.folderForm = AddFolderForm(instance=self.folder)
            self.userPermFormset = UserPermissionFormSet(instance=self.folder)
            self.groupPermFormset = GroupPermissionFormSet(instance=self.folder)
        else:
            self.folderForm = AddFolderForm(request.POST)
            self.userPermFormset = UserPermissionFormSet(request.POST)
            self.groupPermFormset = GroupPermissionFormSet(request.POST)


class AddGroupView(BaseAdminView):
    def post(self, request, *args, **kwargs):
        groupName = request.POST['groupName']
        if groupNameRegex.match(groupName):
            group = get_object_or_None(Group, name=groupName)
            if not group:
                group = Group()
                group.name = groupName
                group.save()
            else:
                messages.error(request, "%s already exists" % groupName)
        else:
            messages.error(request, "Invalid group name.  Must only contain letters, numbers, and underscores")

        return redirect("groupAdmin")


class DeleteGroupView(BaseAdminView):
    def post(self, request, groupName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = Group.objects.get(name=groupName)
        group.delete()

        return redirect('groupAdmin')


class EditGroupView(BaseAdminView):
    def get(self, request, groupName, *args, **kwargs):
        group = Group.objects.get(name=groupName)

        form = EditGroupForm(instance=group)

        self.context['groupName'] = groupName
        self.context['form'] = form
        return render(request, 'admin/edit_group.html', self.context)

    def post(self, request, groupName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        form = EditGroupForm(request.POST)
        if form.is_valid():
            group = Group.objects.get(name=groupName)
            group.user_set.clear()

            for userName in form.cleaned_data['users']:
                user = User.objects.get(username=userName)
                group.user_set.add(user)
            group.save()
        else:
            reqLogger = getReqLogger()
            reqLogger.error('form.errors = %s', form.errors)

        return redirect('groupAdmin')


class GroupAdminView(BaseAdminView):
    def get(self, request, *args, **kwargs):
        groups = []
        for group in Group.objects.all():
            groups.append(group.name)

        self.context['groups'] = groups
        return render(request, 'admin/group_admin.html', self.context)


class DeleteUserView(BaseAdminView):
    def post(self, request, *args, **kwargs):
        redirectUrl = "userAdmin"

        if request.user.username == request.POST['userToDelete']:
            messages.error(request, "Unable to delete current user")
        else:
            user = User.objects.get(username=request.POST['userToDelete'])
            logger.info("Deleting user %s", user)
            user.delete()

        return redirect(redirectUrl)


class UserAdminView(BaseAdminView):
    def get(self, request, *args, **kwargs):
        self.context['users'] = User.objects.all()
        return render(request, 'admin/user_admin.html', self.context)


class AbstractUserView(BaseAdminView, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = None

    @abstractmethod
    def initForm(self, request):
        pass

    def get(self, request, title, *args, **kwargs):
        self.title = title
        if not self.form:
            self.initForm(request)

        self.appendFormErrors(self.form)

        if self.form.instance:
            self.context['username'] = self.form.instance.username
        self.context['form'] = self.form
        self.context['title'] = self.title
        return render(request, 'admin/add_edit_user.html', self.context)

    def post(self, request, title, *args, **kwargs):
        self.title = title
        self.initForm(request)

        with transaction.atomic():
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
                reqLogger.error('form.errors = %s', self.form.errors)
                return self.get(request, *args, **kwargs)

        return redirect("userAdmin")


class EditUserView(AbstractUserView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initForm(self, request):
        if request.method == "GET":
            userName = request.GET['userName']
            user = User.objects.get(username=userName)
            self.form = EditUserForm(instance=user)
        else:
            user = User.objects.get(pk=request.POST['userPk'])
            self.form = EditUserForm(request.POST, instance=user)


class AddUserView(AbstractUserView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initForm(self, request):
        if request.method == "GET":
            self.form = AddUserForm()
        else:
            self.form = AddUserForm(request.POST)


class ChangePasswordView(BaseAdminView):
    def get(self, request, *args, **kwargs):
        return render(request, 'admin/change_password.html', self.context)


class ChangePasswordResultView(BaseAdminView):
    def get(self, request, *args, **kwargs):
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

        if errorMessage:
            messages.error(request, errorMessage)
            self.reqLogger.warn(errorMessage)
            return render(request, 'admin/change_password_fail.html', self.context)
        else:
            return render(request, 'admin/change_password_success.html', self.context)
