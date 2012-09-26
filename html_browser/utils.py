from urllib import quote_plus
import os
from genericpath import getsize, getmtime
from operator import attrgetter  
from constants import _constants as const
from datetime import datetime, timedelta
from django.contrib.auth.models import User, Group
from html_browser.models import Folder
from shutil import copy2, move, copytree, rmtree
from zipfile import ZipFile
import zipfile
from sendfile import sendfile
from glob import glob
from html_browser_site import settings
from django import forms

filesToDelete = []

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
        self.lastModifyTime = lastModifyTime.strftime('%Y-%m-%d %I:%M:%S %p')
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


def getPath(folderPath, path):
    path = path.strip()
    if path == '/':
        path = ''
    dirPath = folderPath.strip() + path
    if not dirPath.endswith('/'):
        dirPath += '/'
    return dirPath

def getCurrentDirEntries(folder, path):
    dirPath = getPath(folder.localPath, path)    
    
    dirEntries = []
    fileEntries = []
    
    os.chdir(dirPath)
    for fileName in os.listdir("."):
        try:
            filePath = dirPath + fileName
            if os.path.isdir(fileName):
                dirEntries.append(DirEntry(True, fileName, getsize(filePath), datetime.fromtimestamp(getmtime(filePath)), folder.name, path, 'details'))
            else:
                fileEntries.append(DirEntry(False, fileName, getsize(filePath), datetime.fromtimestamp(getmtime(filePath)), folder.name, path, 'details'))
        except OSError:
            pass
            
    dirEntries.sort(key=attrgetter('name'))
    fileEntries.sort(key=attrgetter('name'))
    
    dirEntries.extend(fileEntries)
    
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

class Clipboard():
    def __init__(self, currentFolder, currentPath, entries, clipboardType):
        self.currentFolder = currentFolder
        self.currentPath = currentPath
        self.clipboardType = clipboardType
        self.entries = entries.split(',')    
        
class CopyPasteException(Exception):
    pass
    
def handlePaste(currentFolder, currentPath, clipboard):
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    clipboardFolder = Folder.objects.filter(name=clipboard.currentFolder)[0]
    
    dest = getPath(folder.localPath, currentPath)
    
    for entry in clipboard.entries:
        source = getPath(clipboardFolder.localPath, clipboard.currentPath) + entry        
        if clipboard.clipboardType == 'COPY':
            if os.path.isdir(source):
                copytree(source, dest + entry)
            else:
                copy2(source, dest)
        elif clipboard.clipboardType == 'CUT':
            move(source, dest)
        else:
            raise CopyPasteException()
        
def handleDelete(folder, currentPath, entries):
    currentDirPath = getPath(folder.localPath, currentPath)
    
    for entry in entries.split(','):
        entryPath = currentDirPath + entry
        
        if os.path.isdir(entryPath):
            rmtree(entryPath)
        else:
            os.remove(entryPath)
            
def handleRename(folder, currentPath, fileName, newName):
    source = getPath(folder.localPath, currentPath) + fileName
    dest = getPath(folder.localPath, currentPath) + newName
    move(source, dest)
    
def handleDownloadZip(request):
    currentFolder = request.GET['currentFolder']
    currentPath = request.GET['currentPath']
    folder = Folder.objects.filter(name=currentFolder)[0]
    entries = request.REQUEST['files'] 
        
    compression = zipfile.ZIP_DEFLATED
    
    fileName = os.tempnam(None, 'download') + '.zip'    
        
    zipFile = ZipFile(fileName, mode='w', compression=compression)
    
    basePath = getPath(folder.localPath, currentPath)
    for entry in entries.split(','):
        path = getPath(folder.localPath, currentPath) + entry
        if os.path.isfile(path):
            __addFileToZip__(zipFile, path, basePath)
        else:
            addFolderToZip(zipFile, path)
        
    zipFile.close()
    
    filesToDelete.append((fileName, datetime.now()))
    
    return sendfile(request, fileName, attachment=True)
            
            
            
def __addFileToZip__(zipFile, fileToAdd, basePath):
    arcName = fileToAdd.replace(basePath, '')
    zipFile.write(fileToAdd, arcName, compress_type=zipfile.ZIP_DEFLATED)
    
def addFolderToZip(zipFile, folder):    
    __addFolderToZip__(zipFile, folder, folder)    
        
def __addFolderToZip__(zipFile, folder, basePath):
    for f in glob(folder + "/*"):
        if os.path.isfile(f):
            arcName = f.replace(basePath, '')
            zipFile.write(f, arcName, compress_type=zipfile.ZIP_DEFLATED)
        elif os.path.isdir(f):
            __addFolderToZip__(zipFile, f, basePath)
            
def deleteOldFiles():
    now = datetime.now()
    while len(filesToDelete) > 0:
        delta = now - filesToDelete[0][1]
        if delta > timedelta(minutes=10):
            os.remove(filesToDelete.pop(0)[0])
        else:
            return
        
def handleFileUpload(f, folder, currentPath):
    fileName = getPath(folder.localPath, currentPath) + f.name
    dest = open(fileName, 'w')
    
    for chunk in f.chunks():
        dest.write(chunk)
        
    dest.close()
    return fileName
    
def handleZipUpload(f, folder, currentPath):
    fileName = handleFileUpload(f, folder, currentPath)  
    zipFile = ZipFile(fileName, mode='r')
    entries = zipFile.infolist()
    
    localPath = getPath(folder.localPath, currentPath)
    
    for entry in entries:
        zipFile.extract(entry, localPath)
        
    zipFile.close()
    
    os.remove(fileName)
            