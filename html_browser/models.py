from django.db import models
from django.contrib.auth.models import User, Group
from urllib.parse import quote_plus

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

viewableChoices = [
    (VIEWABLE_BY_PERMISSION, 'View authorization set by user and group permissions'),
    (VIEWABLE_BY_EVERYONE, 'Viewable by any registered user'),
    (VIEWABLE_BY_ANONYMOUS, 'Viewable by anonymous users'),
]


class Folder(models.Model):
    name = models.CharField(max_length=100, unique=True)
    localPath = models.CharField(max_length=100, unique=True)
    viewOption = models.CharField(max_length=1,
                                  choices=viewableChoices,
                                  default=VIEWABLE_BY_PERMISSION)

    def __unicode__(self):
        return self.name

    def getNameAsHtml(self):
        return quote_plus(self.name)

    def __checkUserPerm__(self, user, desiredPerm):
        if user.is_superuser:
            return True
        else:
            perms = self.userpermission_set.filter(user__username=user.username)
            for perm in perms:
                if perm.permission >= desiredPerm:
                    return True
            return False

    def __checkGroupPerm__(self, user, desiredPerm):
        for perm in self.grouppermission_set.all():
            if perm.group in user.groups.all():
                if perm.permission >= desiredPerm:
                    return True
        return False

    def userCanRead(self, user):
        if self.viewOption == VIEWABLE_BY_ANONYMOUS:
            return True
        elif self.viewOption == VIEWABLE_BY_EVERYONE and user is not None and user.is_authenticated:
            return True
        else:
            canRead = self.__checkUserPerm__(user, CAN_READ)
            if not canRead:
                canRead = self.__checkGroupPerm__(user, CAN_READ)

            return canRead

    def userCanWrite(self, user):
        return self.__checkUserPerm__(user, CAN_WRITE) or self.__checkGroupPerm__(user, CAN_WRITE)

    def userCanDelete(self, user):
        return self.__checkUserPerm__(user, CAN_DELETE) or self.__checkGroupPerm__(user, CAN_DELETE)


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

    def __str__(self):
        return " ".join([self.folder.name, self.user.username, str(self.permission)])

    def canRead(self):
        return self.permission >= CAN_READ

    class Meta:
        unique_together = ('folder', 'user')


class GroupPermission(Permission):
    group = models.ForeignKey(Group,
                              on_delete=models.CASCADE)

    def __str__(self):
        return " ".join([self.folder.name, self.group.name, str(self.permission)])

    class Meta:
        unique_together = ('folder', 'group')


class FilesToDelete(models.Model):
    filePath = models.CharField(max_length=250)
    time = models.DateTimeField(auto_now=True)
