from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, TEMPLATE_PACK, Button, Layout,
                                 LayoutObject, Submit)
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.template.loader import render_to_string
from django.urls import reverse

from html_browser.models import (Folder, Group, GroupPermission, User,
                                 UserPermission)


class Formset(LayoutObject):
    """
    Layout object. It renders an entire formset, as though it were a Field.

    Example::

    Formset("attached_files_formset")
    """

    template = f"{TEMPLATE_PACK}/table_inline_formset.html"

    def __init__(self, formset_name_in_context, template=None, formset_id=None):
        self.formset_name_in_context = formset_name_in_context
        self.formset_id = formset_id

        # crispy_forms/layout.py:302 requires us to have a fields property
        self.fields = []

        # Overrides class variable with an instance level variable
        if template:
            self.template = template

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK): #pylint: disable=unused-argument
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
        self.fields['local_path'].label = 'Local Path'
        self.fields['view_option'].label = 'View Option'

        add_user_perm_html = HTML('''<br><a href='#' onclick="addUserPermRow();return false;">Add User Permission</a>''')
        add_group_perm_html = HTML('''<br><a href='#' onclick="addGroupPermRow();return false;">Add Group Permission</a><br><br>''')

        self.helper.layout = Layout('name',
                                    'local_path',
                                    'view_option',
                                    Formset('userPermFormset',
                                            template='admin/perm_crispy/table_inline_formset.html',
                                            formset_id='user_perm_formset'),
                                    add_user_perm_html,
                                    Formset('groupPermFormset',
                                            template='admin/perm_crispy/table_inline_formset.html',
                                            formset_id='group_perm_formset'),
                                    add_group_perm_html)

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

        self.helper.add_input(Button('delete', 'Delete Folder', css_class='btn', onclick=f"confirmDelete('{instance.name}')"))


class UserPermissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['folder'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        self.helper.form_show_errors = True
        self.helper.form_id = 'user_perm_form'

    def __iter__(self):
        field_order = [self['id'], self['folder'], self['user'], self['permission'], self['DELETE']]
        return iter(field_order)

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
        field_order = [self['id'], self['folder'], self['group'], self['permission'], self['DELETE']]
        return iter(field_order)

    class Meta:
        model = GroupPermission
        fields = "__all__"


class BaseUserPermissionFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = 'user_perm'
        super().__init__(*args, **kwargs)

    def clean(self):
        pass


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


GroupPermissionFormSet = inlineformset_factory(Folder,
                                               GroupPermission,
                                               formset=BaseGroupPermissionFormSet,
                                               form=GroupPermissionForm,
                                               fields="__all__",
                                               extra=1,
                                               can_delete=True)


class EditGroupForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=('Users'),
            is_stacked=False
        )
    )

    class Meta:
        model = Group
        fields = ('name', 'users')

    #pylint: disable=duplicate-code
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_show_errors = True
        self.helper.form_id = 'form'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Button('cancel', 'Cancel', css_class='btn-default', onclick="window.history.back()"))
        self.helper.add_input(Button('deleteGroup', 'Delete Group', css_class='btn'))

        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        initial['users'] = instance.user_set.all()
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        self.helper.form_action = reverse('editGroup', args=[instance.name])

    def save(self, commit=True):
        group = super().save(False)
        if commit:
            group.save()

        return group
