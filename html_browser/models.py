from django.db import models
from django.contrib.auth.models import User, Group  
from urllib import quote_plus

canRead = 'R'
canWrite = 'W'
canDelete = 'D'

permChoices = [
    (canRead, 'Read Only'),
    (canWrite, 'Read/Write'),
    (canDelete, 'Read/Write/Delete')]  

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
                if perm == desiredPerm:
                    return True
            #TODO handle groups
            return False
    
    def userCanRead(self, user):
        return self.__checkUserPerm__(user, canRead)
    
    def userCanWrite(self, user):
        return self.__checkUserPerm__(user, canWrite)
    
    def userCanDelete(self, user):
        return self.__checkUserPerm__(user, canDelete)                    
    
class UserPermission(models.Model):
    user = models.ForeignKey(User)
    folder = models.ForeignKey(Folder)
    permission = models.CharField(max_length = 1,
                                 choices = permChoices,
                                 default = canRead)    
    
    def __str__(self):
        return self.folder.name + " " + self.user.username + " " + str(self.permission)
    
    def canRead(self):
        return self.permission == canRead
    
class GroupPermission(models.Model):
    group = models.ForeignKey(Group)
    folder = models.ForeignKey(Folder)
    permission = models.CharField(max_length = 1,
                                 choices = permChoices,
                                 default = canRead)
    
    def __str__(self):
        return self.folder.name + " " + self.group.name + " " + str(self.permission)    
