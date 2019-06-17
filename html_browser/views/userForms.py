from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Layout, Submit
from django import forms
from django.urls import reverse

from html_browser.models import User


class AddUserForm(forms.ModelForm):
    verifyPassword = forms.CharField(label='Verify Password', widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_show_errors = True
        self.helper.form_id = 'form'
        self.helper.form_method = 'post'
        self.helper.form_action = 'addUser'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-default', onclick="window.history.back()"))

        self.helper.layout = Layout('username', 'password', 'verifyPassword',
                                    'groups', 'first_name', 'last_name', 'email',
                                    'is_superuser', 'is_active')

        super().__init__(*args, **kwargs)

        self.fields['password'].widget = forms.PasswordInput()

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data['password']
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ('username', 'password', 'groups', 'first_name', 'last_name', 'email', 'is_superuser', 'is_active',)


class EditUserForm(AddUserForm):

    userPk = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.add_input(Button('deleteUser', 'Delete User', css_class='btn'))
        self.fields['username'].required = False
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['password'].required = False
        self.fields['verifyPassword'].required = False

        instance = kwargs['instance']
        self.helper.form_action = reverse("editUser", args=[instance.username])
        self.fields['userPk'].initial = instance.pk

        self.Meta.fields = ('userPk',) + self.Meta.fields
