import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Optional

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db import transaction
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render

from .adminViews import BaseAdminView
from .base_view import BaseView
from .userForms import AddUserForm, EditUserForm

logger = logging.getLogger('html_browser.userViews')


class DeleteUserView(BaseAdminView):
    def post(self, request: HttpRequest) -> HttpResponse:
        username = request.POST['username']
        redirect_url = "userAdmin"

        if request.user.username == username:
            messages.error(request, "Unable to delete current user")
        else:
            user = User.objects.get(username=username)
            logger.info("Deleting user %s", user)
            user.delete()

        return redirect(redirect_url)


class UserAdminView(BaseAdminView):
    def get(self, request: HttpRequest) -> HttpResponse:
        self.context['users'] = User.objects.all()
        return render(request, 'admin/user_admin.html', self.context)


class AbstractUserView(BaseAdminView, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs) -> None:
        self.title: str
        self.username: str
        super().__init__(*args, **kwargs)
        self.form: Optional[AddUserForm] = None
        self.user = User

    @abstractmethod
    def initForm(self, request: HttpRequest) -> AddUserForm:
        pass

    def get(self, request: HttpRequest, title: str, username: Optional[str] = None) -> HttpResponse:
        self.title = title

        if username:
            self.username = username
        if not self.form:
            self.form = self.initForm(request)

        self.appendFormErrors(self.form)

        if self.form.instance:
            self.context['username'] = self.form.instance.username
        self.context['form'] = self.form
        self.context['title'] = self.title
        return render(request, 'admin/add_edit_user.html', self.context)

    def post(self, request: HttpRequest, title: str, username: Optional[str] = None) -> HttpResponse: #pylint: disable=keyword-arg-before-vararg
        self.title = title

        if username:
            self.username = username
        self.form = self.initForm(request)

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
                logger.error('form.errors = %s', self.form.errors)
                return self.get(request, title=self.title, username=request.POST['username'])

        return redirect("userAdmin")


class EditUserView(AbstractUserView):
    def initForm(self, request: HttpRequest) -> EditUserForm:
        if request.method == "GET":
            user = User.objects.get(username=self.username)
            self.form = EditUserForm(instance=user)
        else:
            user = User.objects.get(username=request.POST['username'])
            self.form = EditUserForm(request.POST, instance=user)

        #returning self.form to help mypy
        return self.form


class AddUserView(AbstractUserView):
    def initForm(self, request: HttpRequest) -> AddUserForm:
        if request.method == "GET":
            self.form = AddUserForm()
        else:
            self.form = AddUserForm(request.POST)

        #returning self.form to help mypy
        return self.form


class ChangePasswordView(BaseView):
    def get(self, request: HttpRequest) -> HttpResponse:
        self.context['form'] = PasswordChangeForm(request.user) # type: ignore
        return render(request, 'admin/change_password.html', self.context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PasswordChangeForm(request.user, request.POST) # type: ignore
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed')
            return redirect('index')

        messages.error(request, 'Please correct the error below')
        self.context['form'] = form
        return render(request, 'admin/change_password.html', self.context)
