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

class Folder(models.Model):
    name = models.CharField(max_length=100, unique=True)
    localPath = models.CharField(max_length=100, unique=True)
    
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
            if perm.group in user.groups:
                if perm.permission == desiredPerm:
                    return True
        return False
    
    def userCanRead(self, user):
        canRead = self.__checkUserPerm__(user, CAN_READ)
        if canRead:
            return True
        else:
            return self.__checkGroupPerm__(user, CAN_READ)
    
    def userCanWrite(self, user):
        canWrite = self.__checkUserPerm__(user, CAN_WRITE)
        if canWrite:
            return True
        else:
            return self.__checkGroupPerm__(user, CAN_WRITE)
    
    def userCanDelete(self, user):
        canDelete =self.__checkUserPerm__(user, CAN_DELETE)
        if canDelete:
            return True
        else:
            return self.__checkGroupPerm__(user, CAN_DELETE)                    
    
class UserPermission(models.Model):
    user = models.ForeignKey(User)
    folder = models.ForeignKey(Folder)
    permission = models.CharField(max_length = 1,
                                 choices = permChoices,
                                 default = CAN_READ)    
    
    def __str__(self):
        return self.folder.name + " " + self.user.username + " " + str(self.permission)
    
    def canRead(self):
        return self.permission == CAN_READ
    
class GroupPermission(models.Model):
    group = models.ForeignKey(Group)
    folder = models.ForeignKey(Folder)
    permission = models.CharField(max_length = 1,
                                 choices = permChoices,
                                 default = CAN_READ)
    
    def __str__(self):
        return self.folder.name + " " + self.group.name + " " + str(self.permission)    
