from urllib import quote_plus
import os
import sys
from genericpath import getsize, getmtime
from operator import attrgetter  
from constants import _constants as const  

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
        self.size = size
        self.lastModifyTime = lastModifyTime
        self.linkHtml = self.buildHtmlEntry(currentFolder, currentPath, viewType)
        
    def buildHtmlEntry(self, currentFolder, currentPath, viewType):
        currentFolderParam = "currentFolder=" + quote_plus(currentFolder)
        currentPathParam = "currentPath=" + quote_plus(currentPath)
    
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
    dirPath = folder.localPath + path
    if not dirPath.endswith('/'):
        dirPath += '/'
    
    dirEntries = []
    
    os.chdir(dirPath)
    for fileName in os.listdir("."):
        filePath = dirPath + fileName
        if os.path.isdir(fileName):
            dirEntries.append(DirEntry(True, fileName, getsize(filePath), getmtime(filePath), folder.name, path, 'details'))
        else:
            dirEntries.append(DirEntry(False, fileName, getsize(filePath), getmtime(filePath), folder.name, path, 'details'))
            
    dirEntries.sort(key=attrgetter('name'))
    
    return dirEntries
    
