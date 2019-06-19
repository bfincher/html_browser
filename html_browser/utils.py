import html
import json
import logging
import os
import re
from datetime import datetime
from operator import attrgetter
from pathlib import Path
from shutil import rmtree
from urllib.parse import quote_plus, unquote_plus

from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from sorl.thumbnail import get_thumbnail

from html_browser import settings
from html_browser._os import joinPaths
from html_browser.models import Folder

from .constants import _constants as const

logger = logging.getLogger('html_browser.utils')
reqLogger = None

KILOBYTE = 1024.0
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = MEGABYTE * KILOBYTE
thumbnailGeometry = '150x150'

checkBoxEntryRegex = re.compile(r'cb-(.+)')
folderAndPathRegex = re.compile(r'^(\w+)(/(.*))?$')
imageRegexStr = r'.+\.((jpg)|(png)|(bmp))'
imageRegex = re.compile(r'(?i)%s' % imageRegexStr)
imageRegexWithCach = re.compile(r'(?i)cache/%s' % imageRegexStr)


class ThumbnailStorage(FileSystemStorage):
    def __init__(self):
        p = Path(settings.THUMBNAIL_CACHE_DIR)
        if not p.exists():
            p.mkdir(parents=True)
        super().__init__(location=settings.THUMBNAIL_CACHE_DIR)

    def path(self, name):
        if imageRegexWithCach.match(name):
            return joinPaths(self.base_location, name)
        return name


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
            self.absPath = joinPaths(self.folder.localPath, self.relativePath)
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

            self.absPath = joinPaths(self.folder.localPath, self.relativePath)
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


class DirEntry():
    def __init__(self, path, folderAndPath, viewType, skipThumbnail=False):
        self.thumbnailUrl = None
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

        if not skipThumbnail and not self.isDir and viewType == const.thumbnailsViewType and imageRegex.match(self.name):
            self.hasThumbnail = True
            self.imageLinkPath = joinPaths(folderAndPath.folder.localPath, folderAndPath.relativePath, self.name)
        else:
            self.hasThumbnail = False

    def __str__(self):
        _str = """DirEntry:  isDir = {} name = {} nameUrl = {}
                  size = {} lastModifyTime = {} hasThumbnail = {}
                  thumbnailUrl = {}""".format(str(self.isDir),
                                              self.name,
                                              self.nameUrl,
                                              self.size,
                                              self.lastModifyTime,
                                              self.hasThumbnail,
                                              self.getThumbnailUrl())
        return _str

    def __repr__(self):
        return self.__str__()

    def getThumbnailUrl(self):
        if self.hasThumbnail:
            if not self.thumbnailUrl:
                im = get_thumbnail(self.imageLinkPath, thumbnailGeometry)
                self.thumbnailUrl = reverse('thumb', args=[im.name])
            return self.thumbnailUrl
        return None


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

    skipThumbnail = False
    startTime = datetime.now()

    if _dir.endswith('lost+found'):
        return []

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

                delta = datetime.now() - startTime
                skipThumbnail = skipThumbnail or delta.total_seconds() > 45
                if include:
                    fileEntries.append(DirEntry(f, folderAndPath, viewType, skipThumbnail))
        except OSError as ose:
            logger.exception(ose)

        except UnicodeDecodeError as de:
            logger.exception(de)

    dirEntries.sort(key=attrgetter('name'))
    fileEntries.sort(key=attrgetter('name'))

    dirEntries.extend(fileEntries)

    return dirEntries


def replaceEscapedUrl(url):
    url = html.unescape(url)
    return url.replace("(comma)", ",").replace("(ampersand)", "&")


def handleDelete(folderAndPath, entries):
    for entry in entries:
        entryPath = joinPaths(folderAndPath.absPath, replaceEscapedUrl(entry)).encode("utf-8")

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


def getBytesUnit(numBytes):
    if numBytes / GIGABYTE > 1:
        return "GB"
    elif numBytes / MEGABYTE > 1:
        return "MB"
    elif numBytes / KILOBYTE > 1:
        return "KB"
    else:
        return "Bytes"
