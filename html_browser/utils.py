from urllib import quote_plus
import os
from genericpath import getsize, getmtime
from operator import attrgetter  
from constants import _constants as const
from datetime import datetime
from django.contrib.auth.models import User, Group

#debugFile = open('/tmp/debug.txt', 'w')

def getParentDirLink(path, currentFolder):
    if path == '/':
        return const.BASE_URL
    
    if path.endswith('/'):
        path = path[0:-1]
        
    idx = path.rfind('/')
    
    path = path[0:idx]
    
    if len(path) == 0:
        path = '/'
        
    link = const.CONTENT_URL + "?currentFolder=" + quote_plus(currentFolder)
    link += "&currentPath=" + quote_plus(path) 
    
    return link

class DirEntry():
    def __init__(self, isDir, name, size, lastModifyTime, currentFolder, currentPath, viewType):
        self.isDir = isDir
        self.name = name
        
        if isDir:
            self.size = '&nbsp'
        else:
            self.size = str(size)
        self.lastModifyTime = lastModifyTime.strftime('%Y:%m:%d %I:%M:%S %p')
        self.linkHtml = self.buildHtmlEntry(currentFolder, currentPath, viewType)
        
    def buildHtmlEntry(self, currentFolder, currentPath, viewType):
        currentFolderParam = "currentFolder=" + quote_plus(currentFolder)
        currentPathParam = "currentPath=" + quote_plus(currentPath + "/")
    
        html = '<a href="'
    
        if self.isDir:
            #TODo handlw case where something other than detail is chosen
            html += const.CONTENT_URL + "?" + currentFolderParam + "&" + currentPathParam
            
            if currentPath == '/':
                html += quote_plus(self.name)
            else:
                html += quote_plus('/' + self.name)
        elif viewType == "thumbnails":
            pass #TODO IMPLEMENT
        else:
            html += const.DOWNLOAD_URL + "?" + currentFolderParam + "&" + currentPathParam
            html += "&fileName=" + quote_plus(self.name)
            
        html += '"/><img src="'
        
        if viewType == "details" or viewType == "list":
            if self.isDir:
                html += const.IMAGE_URL + 'folder-blue-icon.png"'
            else:
                html += const.IMAGE_URL + 'Document-icon.png"'
        else:
            pass #TODO implement
        
        html += "/>"
        
        if viewType == "thumbnails" or viewType == "list":
            html += "<br>"
            
        html += self.name
        html += "</a>"
        
        return html

def getCurrentDirEntries(folder, path):
    path = path.strip()
    if path == '/':
        path = ''
    dirPath = folder.localPath.strip() + path
    if not dirPath.endswith('/'):
        dirPath += '/'
    
    dirEntries = []
    
    os.chdir(dirPath)
    for fileName in os.listdir("."):
        filePath = dirPath + fileName
        if os.path.isdir(fileName):
            dirEntries.append(DirEntry(True, fileName, getsize(filePath), datetime.fromtimestamp(getmtime(filePath)), folder.name, path, 'details'))
        else:
            dirEntries.append(DirEntry(False, fileName, getsize(filePath), datetime.fromtimestamp(getmtime(filePath)), folder.name, path, 'details'))
            
    dirEntries.sort(key=attrgetter('name'))
    
    return dirEntries

def getUserNames():
    userNames = []
    for user in User.objects.all():
        userNames.append(user.username)
    
    return userNames

def getGroupNames():
    groupNames = []
    for group in Group.objects.all():
        groupNames.append(group.name)
        
    return groupNames

def getGroupNamesForUser(user):
    assert(isinstance(user, User))
    groupNames = []
    
    for group in user.groups.all():
        groupNames.append(group.name)
        
    return groupNames
    
