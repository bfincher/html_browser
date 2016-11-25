import collections
from datetime import datetime, timedelta
import json
import logging
import os
from shutil import copy2, copytree, move
from urllib.parse import quote_plus

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render

from .base_view import BaseContentView, isShowHidden, reverseContentUrl
from html_browser.models import FilesToDelete, Folder
from html_browser.constants import _constants as const
from html_browser.utils import getCurrentDirEntries,\
    getPath, formatBytes, getBytesUnit, replaceEscapedUrl, handleDelete,\
    getCheckedEntries

logger = logging.getLogger('html_browser.content_view')

class ContentView(BaseContentView):

    def _commonGetPost(self, request, *args, **kwargs):
        super(ContentView, self)._commonGetPost(request, *args, **kwargs)
        self.userCanDelete = self.folder.userCanDelete(request.user)
        self.userCanWrite = self.userCanDelete or self.folder.userCanWrite(request.user)
        self.userCanRead = self.userCanWrite or self.folder.userCanRead(request.user)

    def post(self, request, currentFolder, currentPath=None, *args, **kwargs):
        super(ContentView, self).post(request, currentFolder=currentFolder, currentPath=currentPath, *args, **kwargs)

        self.currentFolder = currentFolder
        self.currentPath = currentPath or ''
        action = request.POST['action']
        if action == 'copyToClipboard':
            entries = getCheckedEntries(request.POST)
            request.session['clipboard'] = Clipboard(self.currentFolder, self.currentPath, entries, 'COPY').toJson()
            messages.success(request, 'Items copied to clipboard')
        elif action == 'cutToClipboard':
            if not self.userCanDelete:
                messages.error(request, "You don't have delete permission on this folder")
            else:
                entries = getCheckedEntries(request.POST)
                request.session['clipboard'] = Clipboard(self.currentFolder, self.currentPath, entries, 'CUT').toJson()
                messages.success(request, 'Items copied to clipboard')
        elif action == 'pasteFromClipboard':
            if not self.userCanWrite:
                messages.error(request, "You don't have write permission on this folder")
            else:
                status = handlePaste(self.currentFolder, self.currentPath, Clipboard.fromJson(request.session['clipboard']))
                if status:
                    messages.error(request, status)
                else:
                    messages.success(request, 'Items pasted')
        elif action == 'deleteEntry':
            if not self.userCanDelete:
                messages.error(request, "You don't have delete permission on this folder")
            else:
                handleDelete(self.folder, self.currentPath, getCheckedEntries(request.POST))
                messages.success(request, 'File(s) deleted')
        elif action == 'setViewType':
            viewType = request.POST['viewType']
            request.session['viewType'] = viewType
        elif action == 'mkDir':
            dirName = request.POST['dir']
            os.makedirs(getPath(self.folder.localPath, self.currentPath) + dirName)
        elif action == 'rename':
            self.handleRename(request.POST['file'], request.POST['newName'])
        elif action == 'changeSettings':
            if request.POST['submit'] == "Save":
                request.session['showHidden'] = request.POST['showHidden'] is not None
        else:
            raise RuntimeError('Unknown action %s' % action)

        return redirect(reverseContentUrl(self.currentFolder, self.currentPath))

    def handleRename(self, fileName, newName):
        source = getPath(self.folder.localPath, self.currentPath) + replaceEscapedUrl(fileName)
        dest = getPath(self.folder.localPath, self.currentPath) + replaceEscapedUrl(newName)
        move(source, dest)

    def get(self, request, currentFolder, currentPath=None, *args, **kwargs):
        super(ContentView, self).get(request, currentFolder=currentFolder, currentPath=currentPath, *args, **kwargs)
        self.currentFolder = currentFolder
        self.currentPath = currentPath or ''
        ContentView.deleteOldFiles()

        contentUrl = reverseContentUrl(self.currentFolder, self.currentPath)
        self.breadcrumbs = None
        crumbs = self.currentPath.split("/")
        if len(crumbs) > 1:
            self.breadcrumbs = "<a href=\"%s\">Home</a> " % reverse('index')
            self.breadcrumbs = self.breadcrumbs + "&rsaquo; <a href=\"%s\">%s</a> " % (contentUrl, currentFolder)

            crumbs = self.currentPath.split("/")
            accumulated = ""
            while len(crumbs) > 0:
                crumb = crumbs.pop(0)
                if crumb:
                    accumulated = "/".join([accumulated, crumb])
                    self.breadcrumbs = self.breadcrumbs + "&rsaquo; "
                    if len(crumbs) > 0:
                        self.breadcrumbs = self.breadcrumbs + "<a href=\"%s\">%s</a> ".format(reverseContentUrl(self.currentFolder, accumulated), crumb)
                                                                                         
                    else:
                        self.breadcrumbs = self.breadcrumbs + crumb

        contentFilter = None
        if 'filter' in request.GET:
            contentFilter = request.GET['filter']
            messages.info(request, 'Filtered on %s' % contentFilter)

        self.context['userCanRead'] = str(self.userCanRead).lower()
        self.context['userCanWrite'] = str(self.userCanWrite).lower()
        self.context['userCanDelete'] = str(self.userCanDelete).lower()
        self.context['breadcrumbs'] = self.breadcrumbs
        self.context['showHidden'] = isShowHidden(request)

#        if 'search' in request.GET:
#            search = request.GET['search']
#            return self._handleSearch(request, search)

        currentDirEntries = getCurrentDirEntries(self.folder, self.currentPath, isShowHidden(request), contentFilter)

        viewType = request.session.get('viewType', const.viewTypes[0])

        diskFreePct = getDiskPercentFree(getPath(self.folder.localPath, self.currentPath))
        diskUsage = getDiskUsageFormatted(getPath(self.folder.localPath, self.currentPath))

        parentDirLink = getParentDirLink(self.currentPath, self.currentFolder)
        self.context['parentDirLink'] = parentDirLink
        self.context['viewTypes'] = const.viewTypes
        self.context['selectedViewType'] = viewType
        self.context['currentDirEntries'] = currentDirEntries
        self.context['diskFreePct'] = diskFreePct
        self.context['diskFree'] = diskUsage.freeformatted
        self.context['diskUsed'] = diskUsage.usedformatted
        self.context['diskTotal'] = diskUsage.totalformatted
        self.context['diskUnit'] = diskUsage.unit

        if viewType == const.detailsViewType:
            template = 'content_detail.html'
        elif viewType == const.listViewType:
            template = 'content_list.html'
        else:
            template = 'content_thumbnail.html'
        return render(request, template, self.context)

#    def _handleSearch(self, request, search):
#        currentDirEntries= getCurrentDirEntriesSearch(self.folder, self.currentPath, BaseView.isShowHidden(request), search)

#        self.context['currentDirEntries'] = currentDirEntries

#        return render(request, "content_search.html", self.context)

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


def getDiskPercentFree(path):
    du = getDiskUsage(path)
    free = du.free / 1.0
    total = du.free + du.used / 1.0
    pct = free / total
    pct = pct * 100.0
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

        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
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
    if path == '/' or path == '':
        return reverse('index')

    if path.endswith('/'):
        path = path[0:-1]

    idx = path.rfind('/')
    if idx == -1:
        path = ''
    else:
        path = path[0:idx]

    link = reverseContentUrl(currentFolder, path)

    return link


class Clipboard():
    def __init__(self, currentFolder, currentPath, entries, clipboardType):
        self.currentFolder = currentFolder
        self.currentPath = currentPath
        self.clipboardType = clipboardType
        self.entries = entries

    @staticmethod
    def fromJson(jsonStr):
        dictData = json.loads(jsonStr)
        return Clipboard(dictData['currentFolder'], dictData['currentPath'], dictData['entries'], dictData['clipboardType'])

    def toJson(self):
        result = {'currentFolder': self.currentFolder,
                  'currentPath': self.currentPath,
                  'clipboardType': self.clipboardType,
                  'entries': self.entries}

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
