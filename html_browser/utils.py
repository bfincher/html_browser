from urllib.parse import quote_plus
import os
from datetime import datetime
from operator import attrgetter
from .constants import _constants as const
from django.contrib.auth.models import User, Group
from html_browser.models import Folder, UserPermission,\
    GroupPermission, FilesToDelete
from pathlib import Path
from shutil import rmtree
import tempfile
from zipfile import ZipFile
import zipfile
from sendfile import sendfile
from html_browser_site.settings import THUMBNAIL_DIR
import html.parser

import re
import logging
from logging import DEBUG

logger = logging.getLogger('html_browser.utils')
reqLogger = None

KILOBYTE = 1024.0
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = MEGABYTE * KILOBYTE

checkBoxEntryRegex = re.compile(r'cb-(.+)')


def getCheckedEntries(requestDict):
    entries = []
    for key in requestDict:
        match = checkBoxEntryRegex.match(key)
        if match and requestDict[key] == 'on':
            entries.append(match.group(1))

    return entries


class DirEntry():
    def __init__(self, path, folder, currentPath):
        self.isDir = path.is_dir()
        self.name = path.name
        self.nameUrl = self.name.replace('&', '&amp;')
        self.nameUrl = quote_plus(self.name)

        self.currentPathOrig = currentPath
        self.currentPath = quote_plus(currentPath)

        stat = path.stat()
        if self.isDir:
            self.size = '&nbsp'
        else:
            size = stat.st_size
            self.size = formatBytes(size)
            self.sizeNumeric = size

        lastModifyTime = datetime.fromtimestamp(stat.st_mtime)
        self.lastModifyTime = lastModifyTime.strftime('%Y-%m-%d %I:%M:%S %p')

        try:
            thumbPath = "/".join([THUMBNAIL_DIR,
                                  folder.name,
                                  currentPath,
                                  self.name])

            if os.path.exists(thumbPath):
                self.hasThumbnail = True
                self.thumbnailUrl = "/".join(
                    [const.THUMBNAIL_URL + folder.name,
                     currentPath,
                     self.name])
            else:
                self.hasThumbnail = False
                self.thumbnailUrl = None

        except UnicodeDecodeError as de:
            logger.exception(de)

    def __str__(self):
        return "DirEntry:  isDir = %s name = %s nameUrl = %s " +\
        "currentPath = %s currentPathOrig = %s size = %s " +\
        "lastModifyTime = %s hasThumbnail = %s thumbnailUrl = %s" % \
            (str(self.isDir), self.name, self.nameUrl, self.currentPath,
                self.currentPathOrig, self.size, self.lastModifyTime,
                self.hasThumbnail, self.thumbnailUrl)


def getPath(folderPath, path):
    path = path.strip()
    if path == '/':
        path = ''
    dirPath = os.path.join(folderPath.strip(), path)
    if not dirPath.endswith('/'):
        dirPath += '/'
    return dirPath
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

def getCurrentDirEntries(folder, path, showHidden, contentFilter=None):
    dirPath = getPath(folder.localPath, path)
    dirEntries = []
    fileEntries = []

    for f in Path(dirPath).iterdir():
        if not showHidden and f.name.startswith('.'):
            continue
        try:
            if f.is_dir():
                dirEntries.append(DirEntry(f, folder, path))
            else:
                include = False
                if contentFilter:
                    tempFilter = contentFilter.replace('.', '\.')
                    tempFilter = tempFilter.replace('*', '.*')
                    if re.search(tempFilter, f.name):
                        include = True
                else:
                    include = True

                if include:
                    fileEntries.append(DirEntry(f, folder, path))
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


def handleDelete(folder, currentPath, entries):
    currentDirPath = replaceEscapedUrl(getPath(folder.localPath, currentPath))

    for entry in entries:
        entryPath = os.path.join(currentDirPath, replaceEscapedUrl(entry)).encode("utf-8")

        if os.path.isdir(entryPath):
            rmtree(entryPath)
        else:
            os.remove(entryPath)


def handleDownloadZip(request):
    currentFolder = request.GET['currentFolder']
    currentPath = request.GET['currentPath']
    folder = Folder.objects.filter(name=currentFolder)[0]

    compression = zipfile.ZIP_DEFLATED

    fileName = tempfile.mktemp(prefix="download_", suffix=".zip")

    zipFile = ZipFile(fileName, mode='w', compression=compression)

    basePath = getPath(folder.localPath, currentPath)
    for entry in getCheckedEntries(request.GET):
        path = getPath(folder.localPath, currentPath) + replaceEscapedUrl(entry)
        if os.path.isfile(path):
            __addFileToZip__(zipFile, path, basePath)
        else:
            addFolderToZip(zipFile, path)

    zipFile.close()

    FilesToDelete.objects.create(filePath=fileName)

    return sendfile(request, fileName, attachment=True)


def __addFileToZip__(zipFile, fileToAdd, basePath):
    arcName = fileToAdd.replace(basePath, '')
    zipFile.write(fileToAdd, arcName, compress_type=zipfile.ZIP_DEFLATED)


def addFolderToZip(zipFile, folder):
    __addFolderToZip__(zipFile, Path(folder), folder)


def __addFolderToZip__(zipFile, folder, basePath):
    for f in folder.iterdir():
        if f.is_file():
            arcName = f.as_posix().replace(basePath, '')
            zipFile.write(f, arcName, compress_type=zipfile.ZIP_DEFLATED)
        elif f.is_dir():
            __addFolderToZip__(zipFile, f, basePath)


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



def getReqLogger():
    if not reqLogger:
        global reqLogger
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


def getRequestField(request, field, default=None):
    if request.method == "GET":
        return request.GET.get(field, default)
    else:
        return request.POST.get(field, default)


def getBytesUnit(numBytes):
    if numBytes / GIGABYTE > 1:
        return "GB"
    elif numBytes / MEGABYTE > 1:
        return "MB"
    elif numBytes / KILOBYTE > 1:
        return "KB"
    else:
        return "Bytes"
