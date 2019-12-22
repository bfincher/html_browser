import logging
import re
from abc import ABCMeta, abstractmethod

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.shortcuts import redirect, render

import html_browser
from html_browser.models import CAN_DELETE, CAN_READ, CAN_WRITE, Folder
from html_browser.utils import getReqLogger, get_object_or_None

from .adminForms import (AddFolderForm, EditFolderForm, EditGroupForm,
                         GroupPermissionFormSet, UserPermissionFormSet)
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

for choice in html_browser.models.viewable_choices:
    option = FolderViewOption(choice[0], choice[1])
    folderViewOptions.append(option)


class BaseAdminView(UserPassesTestMixin, BaseView):
    def test_func(self):
        if not self.request.user.is_staff:
            messages.error(self.request, "User is not an admin")
            return False

        return True

    # override parent class handling of no permission.  We don't want an exception, just a redirect
    def handle_no_permission(self):
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())

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
    def get(self, request):
        return render(request, 'admin/admin.html', self.context)


class FolderAdminView(BaseAdminView):
    def get(self, request):
        self.context['folders'] = Folder.objects.all()
        return render(request, 'admin/folder_admin.html', self.context)


class DeleteFolderView(BaseAdminView):
    def post(self, _, folder_name):
        folder = Folder.objects.get(name=folder_name)
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

    def get(self, request, title, folder_name, *args, **kwargs):
        self.title = title
        self.folder_name = folder_name
        return super().get(request, *args, **kwargs)

    def post(self, request, title, folder_name, *args, **kwargs):
        self.title = title
        self.folder_name = folder_name
        self.origLocalPath = Folder.objects.get(name=folder_name).local_path

        return super().post(request, *args, **kwargs)

    def initForms(self, request):
        self.folder = Folder.objects.get(name=self.folder_name)

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


class AddGroupView(BaseAdminView):
    def post(self, request):
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
    def post(self, _, groupName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = Group.objects.get(name=groupName)
        group.delete()

        return redirect('groupAdmin')


class EditGroupView(BaseAdminView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = None

    def get(self, request, groupName):
        group = Group.objects.get(name=groupName)

        if not self.form:
            self.form = EditGroupForm(instance=group)

        self.context['groupName'] = groupName
        self.context['form'] = self.form
        return render(request, 'admin/edit_group.html', self.context)

    def post(self, request, groupName, *args, **kwargs):
        group = Group.objects.get(name=groupName)
        self.form = EditGroupForm(request.POST, instance=group)

        with transaction.atomic():
            if self.form.is_valid():
                group = self.form.save()

                group.user_set.clear()

                for userName in self.form.cleaned_data['users']:
                    user = User.objects.get(username=userName)
                    group.user_set.add(user)

                group.save()
            else:
                reqLogger = getReqLogger()
                reqLogger.error('form.errors = %s', self.form.errors)
                return self.get(request, groupName=groupName, *args, **kwargs)

        return redirect('groupAdmin')


class GroupAdminView(BaseAdminView):
    def get(self, request):
        groups = []
        for group in Group.objects.all():
            groups.append(group.name)

        self.context['groups'] = groups
        return render(request, 'admin/group_admin.html', self.context)
