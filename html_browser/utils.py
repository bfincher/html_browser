from django.core.files.storage import FileSystemStorage
from django.urls import reverse

from .constants import _constants as const
from html_browser.models import Folder
from html_browser_site import settings

import collections
from datetime import datetime
from operator import attrgetter
import html.parser
from pathlib import Path

import json
import logging
import os
import re
from shutil import rmtree
from sorl.thumbnail import get_thumbnail
from urllib.parse import quote_plus, unquote_plus

logger = logging.getLogger('html_browser.utils')
reqLogger = None

KILOBYTE = 1024.0
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = MEGABYTE * KILOBYTE

checkBoxEntryRegex = re.compile(r'cb-(.+)')
folderAndPathRegex = re.compile(r'^(\w+)(/(.*))?$')
imageRegex = re.compile(r'.+\.(?i)((jpg)|(png)|(gif)|(bmp))')


class ThumbnailStorage(FileSystemStorage):
    def __init__(self, **kwargs):
        super().__init__(location=settings.FOLDER_LINK_DIR)


class NoParentException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ArgumentException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FolderAndPathArgumentException(Exception):
    def __init__(self, **kwargs):
        super().__init__("Expected kwargs are (url)|(folderName, path).  Instead found %s" % kwargs)


class FolderAndPath:
    def __init__(self, *args, **kwargs):
        # options for kwargs are (url)|(folderName, path)

        if 'url' in kwargs and len(kwargs) == 1:
            match = folderAndPathRegex.match(kwargs['url'])
            folderName = match.groups()[0]
            self.folder = Folder.objects.get(name=folderName)
            self.relativePath = unquote_plus(match.groups()[2] or '')
            self.absPath = os.path.join(self.folder.localPath, self.relativePath)
            self.url = kwargs['url']
        elif 'path' in kwargs and len(kwargs) == 2:
            if 'folderName' in kwargs:
                self.folder = Folder.objects.get(name=kwargs['folderName'])
            elif 'folder' in kwargs:
                self.folder = kwargs['folder']
            else:
                raise FolderAndPathArgumentException(**kwargs)

            # just in case the path argument already has the folder localpath appended, try to replace the folder.localpath prefix
            self.relativePath = re.sub(r'^%s' % self.folder.localPath, '', kwargs['path'])

            self.absPath = os.path.join(self.folder.localPath, self.relativePath)
            self.url = "%s/%s" % (self.folder.name, self.relativePath)
        else:
            raise FolderAndPathArgumentException(**kwargs)

    def __str__(self):
        return "folder_name = %s, relativePath = %s, absPath = %s, url = %s" % (self.folder.name, self.relativePath, self.absPath, self.url)

    def getParent(self):
        if self.relativePath == '':
            raise NoParentException()

        return FolderAndPath(folderName=self.folder.name, path=os.path.dirname(self.relativePath))

    @staticmethod
    def fromJson(jsonStr):
        dictData = json.loads(jsonStr)
        return FolderAndPath(**dictData)

    def toJson(self):
        result = {'folderName': self.folder.name,
                  'path': self.relativePath}
        return json.dumps(result)

    def __eq__(self, other):
        return self.url == other.url


def getCheckedEntries(requestDict):
    entries = []
    for key in requestDict:
        match = checkBoxEntryRegex.match(key)
        if match and requestDict[key] == 'on':
            entries.append(match.group(1))

    return entries


def getFolderLinkDir(folderName):
    if not os.path.exists(settings.FOLDER_LINK_DIR):
        os.makedirs(settings.FOLDER_LINK_DIR)
    return os.path.join(settings.FOLDER_LINK_DIR, folderName)


class DirEntry():
    def __init__(self, path, folderAndPath, viewType):
        self.isDir = path.is_dir()
        self.name = path.name
        self.nameUrl = self.name.replace('&', '&amp;')
        self.nameUrl = quote_plus(self.name)

        stat = path.stat()
        if self.isDir:
            self.size = '&nbsp'
        else:
            size = stat.st_size
            self.size = formatBytes(size)
            self.sizeNumeric = size

        lastModifyTime = datetime.fromtimestamp(stat.st_mtime)
        self.lastModifyTime = lastModifyTime.strftime('%Y-%m-%d %I:%M:%S %p')

        if not self.isDir and viewType == const.thumbnailsViewType and imageRegex.match(self.name):
            self.hasThumbnail = True
            imageLinkPath = os.path.join(getFolderLinkDir(folderAndPath.folder.name), folderAndPath.relativePath, self.name)
            im = get_thumbnail(imageLinkPath, '150x150')
            self.thumbnailUrl = reverse('thumb', args=[im.name])
        else:
            self.hasThumbnail = False
            self.thumbnailUrl = None

    def __str__(self):
        _str = """DirEntry:  isDir = {} name = {} nameUrl = {}
                  size = {} lastModifyTime = {} hasThumbnail = {}
                  thumbnailUrl = {}""".format(str(self.isDir),
                                              self.name,
                                              self.nameUrl,
                                              self.size,
                                              self.lastModifyTime,
                                              self.hasThumbnail,
                                              self.thumbnailUrl)
        return _str

    def __repr__(self):
        return self.__str__()


#    return dirPath.encode('utf8')

# def getCurrentDirEntriesSearch(folder, path, showHidden, searchRegexStr):
#    if logger.isEnabledFor(DEBUG):
#        logger.debug("getCurrentDirEntriesSearch: folder = %s path = %s searchRegexStr = %s", folder, path, searchRegexStr)

#    searchRegex = re.compile(searchRegexStr)
#    returnList = []
#    thisEntry = DirEntry(True, path, 0, datetime.fromtimestamp(getmtime(getPath(folder.localPath, path))), folder, path)
#    __getCurrentDirEntriesSearch(folder, path, showHidden, searchRegex, thisEntry, returnList)

#    for entry in returnList:
#        entry.name = "/".join([entry.currentPathOrig, entry.name])

#    return returnList

# def __getCurrentDirEntriesSearch(folder, path, showHidden, searchRegex, thisEntry, returnList):
#    if logger.isEnabledFor(DEBUG):
#        logger.debug("getCurrentDirEntriesSearch:  folder = %s path = %s searchRegex = %s thisEntry = %s", folder, path, searchRegex, thisEntry)
#    entries = getCurrentDirEntries(folder, path, showHidden)

#    includeThisDir = False

#    for entry in entries:
#        try:
#            if searchRegex.search(entry.name):
#                if logger.isEnabledFor(DEBUG):
#                    logger.debug("including this dir")
#                includeThisDir = True
#            elif entry.isDir:
#                __getCurrentDirEntriesSearch(folder, "/".join([path, entry.name]), showHidden, searchRegex, entry, returnList)
#        except UnicodeDecodeError as e:
#            logger.error('UnicodeDecodeError: %s', entry.name)


#    if includeThisDir:
#        returnList.append(thisEntry)

def getCurrentDirEntries(folderAndPath, showHidden, viewType, contentFilter=None):
    _dir = folderAndPath.absPath
    if os.path.isfile(_dir):
        _dir = os.path.dirname(_dir)

    dirEntries = []
    fileEntries = []

    for f in Path(_dir).iterdir():
        if not showHidden and f.name.startswith('.'):
            continue
        try:
            if f.is_dir():
                dirEntries.append(DirEntry(f, folderAndPath, viewType))
            else:
                include = False
                if contentFilter:
                    tempFilter = contentFilter.replace('.', r'\.')
                    tempFilter = tempFilter.replace('*', '.*')
                    if re.search(tempFilter, f.name):
                        include = True
                else:
                    include = True

                if include:
                    fileEntries.append(DirEntry(f, folderAndPath, viewType))
        except OSError as ose:
            logger.exception(ose)

        except UnicodeDecodeError as de:
            logger.exception(de)

    dirEntries.sort(key=attrgetter('name'))
    fileEntries.sort(key=attrgetter('name'))

    dirEntries.extend(fileEntries)

    return dirEntries


def replaceEscapedUrl(url):
    h = html.parser.HTMLParser()
    url = h.unescape(url)
    return url.replace("(comma)", ",").replace("(ampersand)", "&")


def handleDelete(folderAndPath, entries):
    for entry in entries:
        entryPath = os.path.join(folderAndPath.absPath, replaceEscapedUrl(entry)).encode("utf-8")

        if os.path.isdir(entryPath):
            rmtree(entryPath)
        else:
            os.remove(entryPath)


def getReqLogger():
    global reqLogger
    if not reqLogger:
        reqLogger = logging.getLogger('django.request')
    return reqLogger


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

        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        if sys.version_info >= (3,) or isinstance(path, str):
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


def getBytesUnit(numBytes):
    if numBytes / GIGABYTE > 1:
        return "GB"
    elif numBytes / MEGABYTE > 1:
        return "MB"
    elif numBytes / KILOBYTE > 1:
        return "KB"
    else:
        return "Bytes"
