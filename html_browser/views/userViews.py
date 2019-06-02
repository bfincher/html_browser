from abc import ABCMeta, abstractmethod
from datetime import datetime
import logging

from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect

from html_browser.utils import getReqLogger
from .userForms import AddUserForm, EditUserForm
from .adminViews import BaseAdminView

logger = logging.getLogger('html_browser.userViews')

class DeleteUserView(BaseAdminView):
    def post(self, request, username, *args, **kwargs):
        redirectUrl = "userAdmin"

        if request.user.username == username:
            messages.error(request, "Unable to delete current user")
        else:
            user = User.objects.get(username=username)
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
        self.user = None

    @abstractmethod
    def initForm(self, request):
        pass

    def get(self, request, *args, **kwargs):
        if not self.form:
            self.initForm(request)

        self.appendFormErrors(self.form)

        if self.form.instance:
            self.context['username'] = self.form.instance.username
        self.context['form'] = self.form
        self.context['title'] = self.title
        return render(request, 'admin/add_edit_user.html', self.context)

    def post(self, request, *args, **kwargs):
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
                return self.get(request, username=self.username, title=self.title, *args, **kwargs)

        return redirect("userAdmin")


class EditUserView(AbstractUserView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get(self, request, title, username, *args, **kwargs):
        self.username = username
        self.title = title
        return super().get(request, *args, **kwargs)
    
    def post(self, request, title, username, *args, **kwargs):
        self.username = username
        self.title = title
        return super().post(request, *args, **kwargs)

    def initForm(self, request):
        if request.method == "GET":
            user = User.objects.get(username=self.username)
            self.form = EditUserForm(instance=user)
        else:
            user = User.objects.get(username=request.POST['username'])
            self.form = EditUserForm(request.POST, instance=user)


class AddUserView(AbstractUserView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def post(self, request, title, *args, **kwargs):
        self.title = title
        return super().post(request, *args, **kwargs)
        
    def get(self, request, title, *args, **kwargs):
        self.title = title
        return super().get(request, *args, **kwargs)

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
