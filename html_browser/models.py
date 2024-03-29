from urllib.parse import quote_plus
from typing import TypeVar, Type, Union

from django.contrib.auth.models import Group, User, AnonymousUser
from django.db import models

# Create a generic variable that can be 'Parent', or any subclass.
T = TypeVar('T', bound='Folder')

CAN_READ = 1
CAN_WRITE = 2
CAN_DELETE = 3

permChoices = [
    (CAN_READ, 'Read Only'),
    (CAN_WRITE, 'Read/Write'),
    (CAN_DELETE, 'Read/Write/Delete')]

VIEWABLE_BY_EVERYONE = 'E'
VIEWABLE_BY_ANONYMOUS = 'A'
VIEWABLE_BY_PERMISSION = 'P'

viewable_choices = [
    (VIEWABLE_BY_PERMISSION, 'View authorization set by user and group permissions'),
    (VIEWABLE_BY_EVERYONE, 'Viewable by any registered user'),
    (VIEWABLE_BY_ANONYMOUS, 'Viewable by anonymous users'),
]


class Folder(models.Model):
    name = models.CharField(max_length=100, unique=True)
    local_path = models.CharField(max_length=100, unique=True)
    view_option = models.CharField(max_length=1,
                                   choices=viewable_choices,
                                   default=VIEWABLE_BY_PERMISSION)

    @classmethod
    def create(cls: Type[T], name: str, local_path: str, view_option: str) -> T:
        folder = cls()
        folder.name = name
        folder.local_path = local_path
        folder.view_option = view_option
        return folder

    def __str__(self) -> str:
        return self.name

    def get_name_as_html(self) -> str:
        return quote_plus(self.name)

    def _check_user_perm(self, user: Union[User, AnonymousUser], desired_perm: int) -> bool:
        if user.is_superuser:
            return True

        perms = self.userpermission_set.filter(user__username=user.username)
        for perm in perms:
            if perm.permission >= desired_perm:
                return True
        return False

    def _check_group_perm(self, user: Union[User, AnonymousUser], desired_perm: int) -> bool:
        for perm in self.grouppermission_set.all():
            if perm.group in user.groups.all() and perm.permission >= desired_perm: # type: ignore
                return True
        return False

    def user_can_read(self, user: Union[User, AnonymousUser]) -> bool:
        if self.view_option == VIEWABLE_BY_ANONYMOUS:
            return True
        if self.view_option == VIEWABLE_BY_EVERYONE and user is not None and user.is_authenticated:
            return True

        can_read = self._check_user_perm(user, CAN_READ)
        if not can_read:
            can_read = self._check_group_perm(user, CAN_READ)

        return can_read

    def user_can_write(self, user: Union[User, AnonymousUser]) -> bool:
        return self._check_user_perm(user, CAN_WRITE) or self._check_group_perm(user, CAN_WRITE)

    def user_can_delete(self, user: Union[User, AnonymousUser]) -> bool:
        return self._check_user_perm(user, CAN_DELETE) or self._check_group_perm(user, CAN_DELETE)


class Permission(models.Model):
    folder = models.ForeignKey(Folder,
                               on_delete=models.CASCADE)
    permission = models.SmallIntegerField(choices=permChoices,
                                          default=CAN_READ)

    class Meta:
        abstract = True


class UserPermission(Permission):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)

    def __str__(self) -> str:
        return " ".join([self.folder.name, self.user.username, str(self.permission)]) #pylint: disable=no-member

    def canRead(self) -> bool:
        return self.permission >= CAN_READ

    class Meta:
        unique_together = ('folder', 'user')


class GroupPermission(Permission):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return " ".join([self.folder.name, self.group.name, str(self.permission)])

    class Meta:
        unique_together = ('folder', 'group')


class FilesToDelete(models.Model):
    file_path = models.CharField(max_length=250)
    time = models.DateTimeField(auto_now=True)
