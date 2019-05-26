from django import forms
from django.urls import reverse
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.template.loader import render_to_string
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button, Layout, LayoutObject, TEMPLATE_PACK, HTML

from html_browser.models import Folder, UserPermission, GroupPermission, User


class Formset(LayoutObject):
    """
    Layout object. It renders an entire formset, as though it were a Field.

    Example::

    Formset("attached_files_formset")
    """

    template = "%s/table_inline_formset.html" % TEMPLATE_PACK

    def __init__(self, formset_name_in_context, template=None, formset_id=None):
        self.formset_name_in_context = formset_name_in_context
        self.formset_id = formset_id

        # crispy_forms/layout.py:302 requires us to have a fields property
        self.fields = []

        # Overrides class variable with an instance level variable
        if template:
            self.template = template

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK):
        formset = context[self.formset_name_in_context]
        return render_to_string(self.template,
                                {'wrapper': self,
                                 'formset': formset,
                                 'form_id': self.formset_id})


class AddFolderForm(forms.ModelForm):

    class Meta:
        model = Folder
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_show_errors = True
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Folder Name'
        self.fields['localPath'].label = 'Local Path'
        self.fields['viewOption'].label = 'View Option'

        addUserPermHtml = HTML('''<br><a href='#' onclick="addUserPermRow();return false;">Add User Permission</a>''')
        addGroupPermHtml = HTML('''<br><a href='#' onclick="addGroupPermRow();return false;">Add Group Permission</a><br><br>''')

        self.helper.layout = Layout('name',
                                    'localPath',
                                    'viewOption',
                                    Formset('userPermFormset',
                                            template='admin/perm_crispy/table_inline_formset.html',
                                            formset_id='user_perm_formset'),
                                    addUserPermHtml,
                                    Formset('groupPermFormset',
                                            template='admin/perm_crispy/table_inline_formset.html',
                                            formset_id='group_perm_formset'),
                                    addGroupPermHtml)

        self.helper.form_method = 'post'
        self.helper.form_action = 'addFolder'

        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-default', onclick="window.history.back()"))


class EditFolderForm(AddFolderForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget = forms.HiddenInput()

        instance = kwargs['instance']
        self.helper.form_action = reverse('editFolder', args=[instance.name])

        self.helper.add_input(Button('delete', 'Delete Folder', css_class='btn', onclick="confirmDelete('%s')" % instance.name))


class UserPermissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['folder'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        self.helper.form_show_errors = True
        self.helper.form_id = 'user_perm_form'

    def __iter__(self):
        fieldOrder = [self['id'], self['folder'], self['user'], self['permission'], self['DELETE']]
        return iter(fieldOrder)

    class Meta:
        model = UserPermission
        fields = "__all__"


class GroupPermissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['folder'].widget = forms.HiddenInput()
        self.helper = FormHelper()
        self.helper.form_show_errors = True
        self.helper.form_id = 'group_perm_form'

    def __iter__(self):
        fieldOrder = [self['id'], self['folder'], self['group'], self['permission'], self['DELETE']]
        return iter(fieldOrder)

    class Meta:
        model = GroupPermission
        fields = "__all__"


class BaseUserPermissionFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = 'user_perm'
        super().__init__(*args, **kwargs)

    def clean(self):
        pass
        # TODO implement


UserPermissionFormSet = inlineformset_factory(Folder,
                                              UserPermission,
                                              formset=BaseUserPermissionFormSet,
                                              form=UserPermissionForm,
                                              fields="__all__",
                                              extra=1,
                                              can_delete=True)


class BaseGroupPermissionFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = 'group_perm'
        super().__init__(*args, **kwargs)

    def clean(self):
        pass
        # TODO implement


GroupPermissionFormSet = inlineformset_factory(Folder,
                                               GroupPermission,
                                               formset=BaseGroupPermissionFormSet,
                                               form=GroupPermissionForm,
                                               fields="__all__",
                                               extra=1,
                                               can_delete=True)


class EditGroupForm(forms.Form):
    groupName = forms.CharField(required=False, widget=forms.HiddenInput())

    users = None

    def createUsers():
        users = []
        for user in User.objects.all():
            users.append((user.username, user.username))

        users = forms.MultipleChoiceField(choices=users,
                                          required=False,
                                          widget=forms.CheckboxSelectMultiple)
        return users

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'form'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-default', onclick="window.history.back()"))
        self.helper.add_input(Button('deleteGroup', 'Delete Group', css_class='btn'))
        self.users = EditGroupForm.createUsers()

        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            self.helper.form_action = reverse('editGroup', args=[instance.name])
            activeUsers = []

            for user in User.objects.filter(groups__id=instance.id):
                activeUsers.append(user.username)

            self.users.initial = activeUsers
            self.fields['groupName'].initial = instance.name


class AddUserForm(forms.ModelForm):
    verifyPassword = forms.CharField(label='Verify Password', widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
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
        self.helper.form_action = "editUser"
        self.helper.add_input(Button('deleteUser', 'Delete User', css_class='btn'))
        self.fields['username'].required = False
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['password'].required = False
        self.fields['verifyPassword'].required = False

        instance = kwargs['instance']
        self.fields['userPk'].initial = instance.pk

        self.Meta.fields = ('userPk',) + self.Meta.fields
