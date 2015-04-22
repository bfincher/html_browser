from urllib import quote_plus
import os
from genericpath import getsize, getmtime
from operator import attrgetter  
from constants import _constants as const
from datetime import datetime, timedelta
from django.contrib.auth.models import User, Group
from html_browser.models import Folder, UserPermission, GroupPermission
from shutil import copy2, move, copytree, rmtree
from zipfile import ZipFile
import zipfile
from sendfile import sendfile
from html_browser_site.settings import THUMBNAIL_DIR
from math import floor
import sh
import json

import collections
import re
import logging
from logging import DEBUG
from annoying.functions import get_object_or_None

logger = logging.getLogger('html_browser.utils')
filesToDelete = []

KILOBYTE = 1024.0
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = MEGABYTE * KILOBYTE

_permMap = {'read' : 'R', 'write' : 'W', 'delete' : 'D'}

def getParentDirLink(path, currentFolder):
    if path == '/':
        return const.BASE_URL
    
    if path.endswith('/'):
        path = path[0:-1]
        
    idx = path.rfind('/')
    
    path = path[0:idx]
    
    if len(path) == 0:
        path = '/'
        
    link = "%s?currentFolder=%s&currentPath=%s" % (const.CONTENT_URL, quote_plus(currentFolder), quote_plus(path))
    
    return link

class DirEntry():
    def __init__(self, isDir, name, size, lastModifyTime, folder, currentPath):
        self.isDir = isDir
        self.name = name
        self.nameUrl = name.replace('&', '&amp;')
        self.nameUrl = quote_plus(self.name)

        self.currentPathOrig = currentPath
        self.currentPath = quote_plus(currentPath)
        
        if isDir:
            self.size = '&nbsp'
            self.sizeInt = 0
        else:
            self.size = formatBytes(size)
            self.sizeNumeric = size
        self.lastModifyTime = lastModifyTime.strftime('%Y-%m-%d %I:%M:%S %p')        
        
        try:
            thumbPath = "/".join([THUMBNAIL_DIR, folder.name, currentPath, name])
        
            if os.path.exists(thumbPath):
                self.hasThumbnail = True
                self.thumbnailUrl = "/".join([const.THUMBNAIL_URL + folder.name, currentPath, name])
            else:
                self.hasThumbnail = False
                self.thumbnailUrl = None

        except UnicodeDecodeError, de:
	        logger.exception(de)

    def __str__(self):
        return "DirEntry:  isDir = %s name = %s nameUrl = %s currentPath = %s currentPathOrig = %s size = %s lastModifyTime = %s hasThumbnail = %s thumbnailUrl = %s" % \
	    (str(self.isDir), self.name, self.nameUrl, self.currentPath, self.currentPathOrig, self.size, self.lastModifyTime, self.hasThumbnail, self.thumbnailUrl)

def getPath(folderPath, path):
    path = path.strip()
    if path == '/':
        path = ''
    dirPath = folderPath.strip() + path
    if not dirPath.endswith('/'):
        dirPath += '/'
    return dirPath.encode('utf8')

def getCurrentDirEntriesSearch(folder, path, showHidden, search):
    if logger.isEnabledFor(DEBUG):
        logger.debug("getCurrentDirEntriesSearch:  folder = %s path = %s search = %s", folder, path, search)
    returnList = []
    thisEntry = DirEntry(True, path, 0, datetime.fromtimestamp(getmtime(getPath(folder.localPath, path))), folder, path)
    __getCurrentDirEntriesSearch(folder, path, showHidden, search, thisEntry, returnList)

    for entry in returnList:
        entry.name = "/".join([entry.currentPathOrig, entry.name])

    return returnList

def __getCurrentDirEntriesSearch(folder, path, showHidden, search, thisEntry, returnList):
    if logger.isEnabledFor(DEBUG):
        logger.debug("getCurrentDirEntriesSearch:  folder = %s path = %s search = %s thisEntry = %s", folder, path, search, thisEntry)
    entries = getCurrentDirEntries(folder, path, showHidden)

    includeThisDir = False

    for entry in entries:
        if entry.isDir:
	    __getCurrentDirEntriesSearch(folder, "/".join([path, entry.name]), showHidden, search, entry, returnList)
        else:
	    if entry.name.find(search) != -1:
                if logger.isEnabledFor(DEBUG):
                    logger.debug("including this dir")
	        includeThisDir = True
    
    if includeThisDir:
        returnList.append(thisEntry)

def getCurrentDirEntries(folder, path, showHidden, filter=None):
    dirPath = getPath(folder.localPath, path)
    dirEntries = []
    fileEntries = []
    
    os.chdir(dirPath)
    for fileName in os.listdir("."):
        if not showHidden and fileName.startswith('.'):
	    continue
        try:
            filePath = dirPath + fileName
            if os.path.isdir(fileName):
                dirEntries.append(DirEntry(True, fileName, getsize(filePath), datetime.fromtimestamp(getmtime(filePath)), folder, path))
            else:
                include = False
                if filter != None:
                    tempFilter = filter.replace('.', '\.')
                    tempFilter = tempFilter.replace('*', '.*')
                    if re.search(tempFilter, fileName):
                        include = True 
                else:
                    include = True

                if include:
                    fileEntries.append(DirEntry(False, fileName, getsize(filePath), datetime.fromtimestamp(getmtime(filePath)), folder, path))
        except OSError, ose:
	    logger.exception(ose)

        except UnicodeDecodeError, de:
	    logger.exception(de)
            
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

        if type(entries) is list:
            self.entries = entries
        else:
            self.entries = entries.split(',')    

    @staticmethod
    def fromJson(jsonStr):
        dictData = json.loads(jsonStr)
        return Clipboard(dictData['currentFolder'], dictData['currentPath'], dictData['entries'], dictData['clipboardType'])

    def toJson(self):
        result = {'currentFolder' : self.currentFolder,
            'currentPath' : self.currentPath,
            'clipboardType' : self.clipboardType,
            'entries' : self.entries}

        return json.dumps(result)
        
class CopyPasteException(Exception):
    pass

def replaceEscapedUrl(url):
    return url.replace("(comma)", ",").replace("(ampersand)", "&")
    
def handlePaste(currentFolder, currentPath, clipboard):
    
    folder = Folder.objects.filter(name=currentFolder)[0]
    clipboardFolder = Folder.objects.filter(name=clipboard.currentFolder)[0]
    
    dest = getPath(folder.localPath, currentPath)
    
    for entry in clipboard.entries:
        source = getPath(clipboardFolder.localPath, clipboard.currentPath) + replaceEscapedUrl(entry)
        if os.path.exists(os.path.join(dest, entry)):
            return "One or more of the items already exists in the destination"
        
    for entry in clipboard.entries:
        source = getPath(clipboardFolder.localPath, clipboard.currentPath) + replaceEscapedUrl(entry)
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
        entryPath = os.path.join(currentDirPath, replaceEscapedUrl(entry)).encode("utf-8")
        
        if os.path.isdir(entryPath):
            rmtree(entryPath)
        else:
            os.remove(entryPath)
            
def handleRename(folder, currentPath, fileName, newName):
    source = getPath(folder.localPath, currentPath) + replaceEscapedUrl(fileName)
    dest = getPath(folder.localPath, currentPath) + replaceEscapedUrl(newName)
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
        path = getPath(folder.localPath, currentPath) + replaceEscapedUrl(entry)
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
    for f in sh.ls("-1", folder):
        f = f.strip()
        f = os.path.join(folder, f)
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

def getDiskPercentFree(path):
    du = getDiskUsage(path)
    free = du.free / 1.0
    total = du.free + du.used / 1.0
    pct = free / total;
    pct = pct * 100.0;
    return "%.2f" % pct + "%" 

def getBytesUnit(numBytes):
    if numBytes / GIGABYTE > 1:
        return "GB"
    elif numBytes / MEGABYTE > 1:
        return "MB"
    elif numBytes / KILOBYTE > 1:
        return "KB"
    else:
        return "Bytes"

def formatBytes(numBytes, forceUnit=None, includeUnitSuffix=True):
    if forceUnit:
        unit = forceUnit
    else:
        unit = getBytesUnit(numBytes)

    if unit == "GB":
        returnValue = "%.2f" % (numBytes / GIGABYTE)
    elif unit == "MB":
        returnValue = "%.2f" % (numBytes / MEGABYTE)
    elif unit == "KB":
        returnValue = "%.2f" % (numBytes / KILOBYTE)
    else:
        returnValue = str(numBytes)

    if includeUnitSuffix and unit != "Bytes":
        return "%s %s" % (returnValue, unit)
    else:
        return returnValue

def getDiskUsageFormatted(path):
    du = getDiskUsage(path)

    _ntuple_diskusage_formatted = collections.namedtuple('usage', 'total totalformatted used usedformatted free freeformatted unit')

    unit = getBytesUnit(du.total)
    total = formatBytes(du.total, unit, False)
    used = formatBytes(du.used, unit, False)
    free = formatBytes(du.free, unit, False)

    return _ntuple_diskusage_formatted(du.total, total, du.used, used, du.free, free, unit)

def getDiskUsage(path):
    _ntuple_diskusage = collections.namedtuple('usage', 'total used free')

    if hasattr(os, 'statvfs'):  # POSIX
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return _ntuple_diskusage(total, used, free)

    elif os.name == 'nt':       # Windows
        import ctypes
        import sys

        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                       ctypes.c_ulonglong()
        if sys.version_info >= (3,) or isinstance(path, unicode):
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
        else:
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
        ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
        if ret == 0:
            raise ctypes.WinError()
        used = total.value - free.value
        return _ntuple_diskusage(total.value, used, free.value)
    else:
        raise NotImplementedError("platform not supported")

def __assignGroupsToUser(user,request):

    user.groups.clear()

    for key in request:
        if key.startswith("isGroup"):
            groupName = key[7:]
            if logger.isEnabledFor(DEBUG):
                logger.debug("processing key %s", key)
                logger.debug("groupName = %s", groupName)
            group = Group.objects.get(name=groupName)
            user.groups.add(group)

def __assignUsersToGroup(group, request):

    group.user_set.clear()

    for key in request.REQUEST:
        if key.startswith("isUser"):
            if logger.isEnabledFor(DEBUG):
                logger.debug("processing key $s", key)
            userName = key[6:]
            user = User.objects.get(username=userName)
            group.user_set.add(user)

def handleEditFolder(request, folder=None):
    if folder == None:
        folderName = request.REQUEST['name']
        folder = Folder.objects.get(name=folderName)

    folder.localPath = request.REQUEST['directory']
    folder.viewOption = request.REQUEST['viewOption']
    folder.save()

    newUsers = {}
    newGroups = {}
    for key in request.REQUEST:
        if key.startswith('user-'):
	    tokens = key.split('-')
	    newUsers[tokens[1]] = tokens[2]
        elif key.startswith('group-'):
	    tokens = key.split('-')
	    newGroups[tokens[1]] = tokens[2]

    for userPerm in UserPermission.objects.filter(folder = folder):
        if newUsers.has_key(userPerm.user.username):
            userPerm.permission = _permMap[newUsers[userPerm.user.username]]
	    userPerm.save()

	    del newUsers[userPerm.user.username]

        else:
	    userPerm.delete()

    for key in newUsers:
        perm = UserPermission()
	perm.folder = folder
	perm.permission = _permMap[newUsers[key]]
	perm.user = User.objects.get(username = key)
	perm.save()
    
    for groupPerm in GroupPermission.objects.filter(folder = folder):
        if newGroups.has_key(groupPerm.group.name):
            groupPerm.permission = _permMap[newGroups[groupPerm.group.name]]
	    groupPerm.save()

	    del newGroups[groupPerm.group.name]

        else:
	    groupPerm.delete()

    for key in newGroups:
        perm = GroupPermission()
	perm.folder = folder
	perm.permission = _permMap[newGroups[key]]
	perm.group = Group.objects.get(name = key)
	perm.save()


def handleAddFolder(request):
    folderName = request.REQUEST['name']
    folder = Folder()
    folder.name = folderName
    handleEditFolder(request, folder)

def handleDeleteFolder(request):
    folderName = request.REQUEST['name']
    folder = Folder.objects.get(name=folderName)
    folder.delete()

def handleEditUser(request):

    userName = request['userName']

    if request.has_key('password'):
        password = request['password']

    isAdmin = request.has_key('isAdministrator')

    user = User.objects.get(username=userName)
    if password:
        user.set_password(password)
    user.is_staff = isAdmin
    user.is_superuser = isAdmin
    user.is_active = True
    user.save()

    __assignGroupsToUser(user, request)
    userGroups = user.groups.all()

    user.save()

def handleAddUser(request):
    userName = request['userName']

    user = get_object_or_None(User, username=userName)
    if user != None:
        return "User %s already exists" % userName

    password = request['password']

    isAdmin = request.has_key('isAdministrator')

    user = User()
    user.username = userName;
    user.set_password(password)
    user.is_staff = isAdmin
    user.is_superuser = isAdmin
    user.is_active = True
    user.save()

    __assignGroupsToUser(user, request)

    user.save()

def handleDeleteUser(request):
    user = User.objects.get(username=request.REQUEST['userToDelete'])
    logger.info("Deleting user %s", user)
    user.delete()

def handleEditGroup(request):
    group = Group.objects.get(name = request.REQUEST['groupName'])
    __assignUsersToGroup(group, request)

def handleAddGroup(request):
    groupName = request.REQUEST['groupName']

    group = get_object_or_None(Group, name=groupName)

    if group != None:
        return "Group %s already exists" % groupName

    group = Group()
    group.name = groupName
    group.save()

def handleDeleteGroup(request):
    groupName = request.REQUEST['groupToDelete']

    group = Group.objects.get(name=groupName)
    group.delete()
