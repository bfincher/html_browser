import collections
from datetime import datetime, timedelta
import json
import os
from shutil import copy2, copytree, move
from urllib import quote_plus

from django.shortcuts import redirect, render

from base_view import BaseView
from html_browser.models import FilesToDelete, Folder
from html_browser.constants import _constants as const
from html_browser.utils import getRequestField, getCurrentDirEntries, getCurrentDirEntriesSearch,\
    getPath, formatBytes, getBytesUnit, replaceEscapedUrl, handleDelete

class ContentView(BaseView):
    def get(self, request, *args, **kwargs):
        return self._get_or_post(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        return self._get_or_post(request, args, kwargs)

    def _get_or_post(self, request, *args, **kwargs):
        self.request = request
        ContentView.deleteOldFiles()
    
        self.getFolder(request)
        self.userCanDelete = self.folder.userCanDelete(self.request.user)
        self.userCanWrite = self.userCanDelete or self.folder.userCanWrite(self.request.user)
        self.userCanRead = self.userCanWrite or self.folder.userCanRead(self.request.user)    
    
        if self.userCanRead == False:
            self.reqLogger.warn("%s not allowed to read %s", self.request.user, self.currentFolder)
            return redirect(const.BASE_URL, 'You are not authorized to view this page')
    
        self.status = ''
        self.statusError = None

        action = getRequestField(self.request,'action')
        if action:
            return self._handleAction(action)
    
        self.status = getRequestField(self.request,'status', '')

        self.statusError = getRequestField(self.request,'statusError')

        self.breadcrumbs = None
        crumbs = self.currentPath.split("/")
        if len(crumbs) > 1:
            self.breadcrumbs = "<a href=\"%s\">Home</a> " % const.BASE_URL
            self.breadcrumbs = self.breadcrumbs + "&rsaquo; <a href=\"%scontent/?currentFolder=%s&currentPath=\">%s</a> " % (const.BASE_URL, self.currentFolder, self.currentFolder)
            crumbs = self.currentPath.split("/")
            accumulated = ""
            while len(crumbs) > 0:
                crumb = crumbs.pop(0)
                if crumb:
                    accumulated = "/".join([accumulated, crumb])
                    self.breadcrumbs = self.breadcrumbs + "&rsaquo; "
                    if len(crumbs) > 0:
                        self.breadcrumbs = self.breadcrumbs + "<a href=\"%scontent/?currentFolder=%s&currentPath=%s\">%s</a> " % (const.BASE_URL, self.currentFolder, accumulated, crumb)
                    else:
                        self.breadcrumbs = self.breadcrumbs + crumb

        contentFilter = getRequestField(self.request,'filter')
        if contentFilter:
            self.status = self.status + ' Filtered on %s' % getRequestField(self.request,'filter')


        self.values = self.buildBaseContext(request)
        self.values['userCanRead'] = str(self.userCanRead).lower()
        self.values['userCanWrite'] = str(self.userCanWrite).lower()
        self.values['userCanDelete'] = str(self.userCanDelete).lower()
        self.values['status'] = self.status
        self.values['breadcrumbs'] = self.breadcrumbs
        self.values['showHidden'] = BaseView.isShowHidden(self.request)

        if self.statusError:
            self.values['statusError'] = True

        search = getRequestField(self.request,'search')
        if search:
            return self._handleSearch(search)

        currentDirEntries = getCurrentDirEntries(self.folder, self.currentPath, BaseView.isShowHidden(self.request), contentFilter)
    
        if self.request.session.has_key('viewType'):
            viewType = self.request.session['viewType']
        else:
            viewType = const.viewTypes[0]                   

        diskFreePct = getDiskPercentFree(getPath(self.folder.localPath, self.currentPath))
        diskUsage = getDiskUsageFormatted(getPath(self.folder.localPath, self.currentPath))

        parentDirLink = getParentDirLink(self.currentPath, self.currentFolder)
        self.values['parentDirLink'] = parentDirLink
        self.values['viewTypes'] = const.viewTypes
        self.values['selectedViewType'] = viewType
        self.values['currentDirEntries'] = currentDirEntries
        self.values['diskFreePct'] = diskFreePct
        self.values['diskFree'] = diskUsage.freeformatted
        self.values['diskUsed'] = diskUsage.usedformatted
        self.values['diskTotal'] = diskUsage.totalformatted
        self.values['diskUnit'] = diskUsage.unit

        if self.statusError:
            self.values['statusError'] = True
    
        if viewType == const.detailsViewType:
            template = 'content_detail.html'
        elif viewType == const.listViewType:
            template = 'content_list.html'
        else:
            template = 'content_thumbnail.html'
        return render(request, template, self.values)
        
    def _handleAction(self, action):
        if action == 'copyToClipboard':
            entries = getRequestField(self.request,'entries')
            self.request.session['clipboard'] = Clipboard(self.currentFolder, self.currentPath, entries, 'COPY').toJson()
            self.status='Items copied to clipboard';
        elif action == 'cutToClipboard':
            if not self.userCanDelete:
                self.status="You don't have delete permission on this folder"
                self.statusError = True
            else:
                entries = getRequestField(self.request,'entries')
                self.request.session['clipboard'] = Clipboard(self.currentFolder, self.currentPath, entries, 'CUT').toJson()
                self.status = 'Items copied to clipboard'
        elif action == 'pasteFromClipboard':
            if not self.userCanWrite:
                self.status = "You don't have write permission on this folder"
                self.statusError = True
            else:
                self.status = handlePaste(self.currentFolder, self.currentPath, Clipboard.fromJson(self.request.session['clipboard']))
                if self.status:
                    self.statusError = True
                else:
                    self.status = 'Items pasted'
        elif action == 'deleteEntry':
            if not self.userCanDelete:
                self.status = "You don't have delete permission on this folder"
                self.statusError = True
            else:
                handleDelete(self.folder, self.currentPath, getRequestField(self.request,'entries'))
                self.status = 'File(s) deleted'
        elif action=='setViewType':
            viewType = getRequestField(self.request,'viewType')
            self.request.session['viewType'] = viewType
        elif action == 'mkDir':
            dirName = getRequestField(self.request,'dir')
            os.makedirs(getPath(self.folder.localPath, self.currentPath) + dirName)
        elif action == 'rename':
            self.handleRename(getRequestField(self.request,'file'), getRequestField(self.request,'newName'))
        elif action == 'changeSettings':
            if getRequestField(self.request,'submit') == "Save":
                self.request.session['showHidden'] = getRequestField(self.request,'showHidden') != None
        else:
            raise RuntimeError('Unknown action %s' % action)
    
        redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=%s" % (const.CONTENT_URL, self.currentFolder, self.currentPath, self.status)

        if self.statusError:
            redirectUrl += "&statusError=%s" % self.statusError

        return redirect(redirectUrl)        

    def _handleSearch(self, search):
        currentDirEntries= getCurrentDirEntriesSearch(self.folder, self.currentPath, BaseView.isShowHidden(self.request), search)

        self.values['currentDirEntries'] = currentDirEntries

        return render(self.request, "content_search.html", self.values)

    @staticmethod
    def deleteOldFiles():
        now = datetime.now()
        for fileToDelete in FilesToDelete.objects.all().order_by('time'):
            delta = now - fileToDelete.time
            if delta > timedelta(minutes=10):
                if os.path.isfile(fileToDelete.filePath):
                    os.remove(fileToDelete.filePath)
                fileToDelete.delete()
            else:
                return

    def handleRename(self, fileName, newName):
        source = getPath(self.folder.localPath, self.currentPath) + replaceEscapedUrl(fileName)
        dest = getPath(self.folder.localPath, self.currentPath) + replaceEscapedUrl(newName)
        move(source, dest)
    

def getDiskPercentFree(path):
    du = getDiskUsage(path)
    free = du.free / 1.0
    total = du.free + du.used / 1.0
    pct = free / total;
    pct = pct * 100.0;
    return "%.2f" % pct + "%" 

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
        
