from django import template
from django.db import models
from django.contrib.auth.models import User, Group  
from urllib import quote_plus

CAN_READ = 'R'
CAN_WRITE = 'W'
CAN_DELETE = 'D'

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
    viewOption = models.CharField(max_length = 1,
                                 choices = viewableChoices,
                                 default = VIEWABLE_BY_PERMISSION)    
    
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
                if perm.permission == desiredPerm:
                    return True
            return False
        
    def __checkGroupPerm__(self, user, desiredPerm):
        for perm in self.grouppermission_set.all():
            if perm.group in user.groups.all():
                if perm.permission == desiredPerm:
                    return True
        return False
    
    def userCanRead(self, user):
        if self.viewOption == VIEWABLE_BY_ANONYMOUS:
            return True
        elif self.viewOption == VIEWABLE_BY_EVERYONE and user != None and user.is_authenticated():
            return True
        else:
            canRead = self.__checkUserPerm__(user, CAN_READ)
            if not canRead:
                canRead = self.__checkGroupPerm__(user, CAN_READ)
            
            if not canRead:
                canRead = self.userCanWrite(user)
            
            return canRead
            
    
    def userCanWrite(self, user):
        canWrite = self.__checkUserPerm__(user, CAN_WRITE)
        if not canWrite:
            canWrite = self.__checkGroupPerm__(user, CAN_WRITE)
            
        if not canWrite:
            canWrite = self.userCanDelete(user)
            
        return canWrite
    
    def userCanDelete(self, user):
        canDelete =self.__checkUserPerm__(user, CAN_DELETE)
        if canDelete:
            return True
        else:
            return self.__checkGroupPerm__(user, CAN_DELETE)                    
    
class Permission(models.Model):
    folder = models.ForeignKey(Folder)
    permission = models.CharField(max_length = 1,
                                 choices = permChoices,
                                 default = CAN_READ)    

    class Meta:
        abstract = True

class UserPermission(Permission):
    user = models.ForeignKey(User)
    
    def __str__(self):
        return self.folder.name + " " + self.user.username + " " + str(self.permission)
    
    def getUserOrGroup(self):
        return "user"

    def getUserOrGroupName(self):
        return user.username

    def canRead(self):
        return self.permission == CAN_READ

class GroupPermission(Permission):
    group = models.ForeignKey(Group)
    
    def __str__(self):
        return self.folder.name + " " + self.group.name + " " + str(self.permission)    

    def getUserOrGroup(self):
        return "group"

    def getUserOrGroupName(self):
        return group.name

