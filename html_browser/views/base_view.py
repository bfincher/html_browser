from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.views import View

from html_browser.constants import _constants as const
from html_browser.models import Folder, FilesToDelete
from html_browser.utils import getCurrentDirEntries, handleDelete,\
    getReqLogger,\
    getCheckedEntries, replaceEscapedUrl,\
    FolderAndPath
from html_browser_site import settings

import json
import logging
from logging import DEBUG
import os
from pathlib import Path
import re
from django_downloadview import sendfile
import tempfile
import zipfile
from zipfile import ZipFile

logger = logging.getLogger('html_browser.base_view')
imageRegex = re.compile("^.*?\.(jpg|png|gif|bmp|avi)$", re.IGNORECASE)


def isShowHidden(request):
    return request.session.get('showHidden', False)


def reverseContentUrl(folderAndPath, viewName='content', extraPath=None):
    folderAndPathUrl = folderAndPath.url.replace('//', '/')
    if folderAndPathUrl.endswith('/'):
        folderAndPathUrl = folderAndPathUrl[:-1]
    args = [folderAndPathUrl]
    if extraPath:
        args.append(extraPath)
    return reverse(viewName, args=args)


class BaseView(View):
    def __init__(self):
        self.reqLogger = getReqLogger()

    def _setup(self, request, *args, **kwargs):
        self.reqLogger.info(self.__class__.__name__)
        self.request = request
        if self.reqLogger.isEnabledFor(DEBUG):
            _dict = None
            if request.method == "GET":
                _dict = request.GET
            else:
                _dict = request.POST

            for key, value in sorted(_dict.items()):
                if key in ['password', 'verifyPassword']:
                    self.reqLogger.debug("%s: ********", key)
                else:
                    self.reqLogger.debug("%s: %s", key, value)

        self.context = {'user': request.user}


class BaseContentView(BaseView):
    def __init__(self, requireWrite=False, requireDelete=False):
        super(BaseContentView, self).__init__()
        self.folderAndPath = None
        self.requireWrite = requireWrite
        self.requireDelete = requireDelete

    def _setup(self, request, *args, **kwargs):
        super(BaseContentView, self)._setup(request, *args, **kwargs)

        if 'folderAndPathUrl' in kwargs:
            self.folderAndPath = FolderAndPath(url=kwargs['folderAndPathUrl'])
        elif 'folderAndPath' in kwargs:
            self.folderAndPath = kwargs['folderAndPath']
        else:
            raise ArgumentException("One of folderandPathUrl or folderAndPath params must be specified")

        self.userCanDelete = self.folderAndPath.folder.userCanDelete(request.user)
        self.userCanWrite = self.userCanDelete or self.folderAndPath.folder.userCanWrite(request.user)
        self.userCanRead = self.userCanWrite or self.folderAndPath.folder.userCanRead(request.user)

        if self.requireDelete and not self.userCanDelete:
            raise PermissionDenied("Delete permission required")
        if self.requireWrite and not self.userCanWrite:
            raise PermissionDenied("Write permission required")
        if not self.userCanRead:
            raise PermissionDenied("Read permission required")

        self.context['folderAndPath'] = self.folderAndPath


class IndexView(BaseView):
    def get(self, request, *args, **kwargs):
        self._setup(request, *args, **kwargs)

        allFolders = Folder.objects.all()
        folders = []
        for folder in allFolders:
            if folder.userCanRead(request.user):
                folders.append(folder)

        self.context['folders'] = folders

        return render(request, 'index.html', self.context)


class LoginView(BaseView):
    def post(self, request, *args, **kwargs):
        self._setup(request, *args, **kwargs)

        userName = request.POST['userName']
        password = request.POST['password']
        user = authenticate(username=userName, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                if self.reqLogger.isEnabledFor(DEBUG):
                    self.reqLogger.debug("%s authenticated", user)
            else:
                self.reqLogger.warn("%s attempted to log in to a disabled account", user)
                messages.error(request, 'Account has been disabled')
        else:
            messages.error(request, 'Invalid login')

        return redirect('index')


class LogoutView(BaseView):
    def get(self, request, *args, **kwargs):
        self._setup(request, *args, **kwargs)
        auth_logout(request)
        return redirect('index')


class DownloadView(BaseContentView):
    def get(self, request, folderAndPathUrl, fileName, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)
        return sendfile(request,
                        os.path.join(self.folderAndPath.absPath, fileName),
                        attachment=True)


class DownloadImageView(BaseContentView):
    def get(self, request, folderAndPathUrl, fileName, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)
        return sendfile(request, os.path.join(self.folderAndPath.absPath, fileName), attachment=False)


class ThumbView(BaseView):
    def get(self, request, path, *args, **kwargs):
        self._setup(request, *args, **kwargs)
        file = os.path.join(settings.THUMBNAIL_CACHE_DIR, path)
        return sendfile(request, file, attachment=False)


class DownloadZipView(BaseContentView):
    def get(self, request, folderAndPathUrl, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)

        compression = zipfile.ZIP_DEFLATED
        fileName = tempfile.mktemp(prefix="download_", suffix=".zip")
        self.zipFile = ZipFile(fileName, mode='w', compression=compression)

        for entry in getCheckedEntries(request.GET):
            path = os.path.join(self.folderAndPath.absPath, replaceEscapedUrl(entry))
            if os.path.isfile(path):
                self.__addFileToZip__(path)
            else:
                self.__addFolderToZip__(Path(path))

        self.zipFile.close()

        FilesToDelete.objects.create(filePath=fileName)

        return sendfile(request, fileName, attachment=True)

    def __addFileToZip__(self, fileToAdd):
        arcName = fileToAdd.replace(self.folderAndPath.absPath, '')
        self.zipFile.write(fileToAdd, arcName, compress_type=zipfile.ZIP_DEFLATED)

    def __addFolderToZip__(self, folder):
        for f in folder.iterdir():
            if f.is_file():
                arcName = f.as_posix().replace(self.folderAndPath.absPath, '')
                self.zipFile.write(f.as_posix(), arcName, compress_type=zipfile.ZIP_DEFLATED)
            elif f.is_dir():
                self.__addFolderToZip__(f)


class UploadView(BaseContentView):
    def __init__(self):
        super(UploadView, self).__init__(requireWrite=True)

    def get(self, request, folderAndPathUrl, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)

        self.context['viewTypes'] = const.viewTypes

        return render(request, 'upload.html', self.context)

    def post(self, request, folderAndPathUrl, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)

        action = request.POST['action']
        if action == 'uploadFile':
            self._handleFileUpload(request.FILES['upload1'])
            messages.success(request, 'File uploaded')
        elif action == 'uploadZip':
            self._handleZipUpload(request.FILES['zipupload1'])
            messages.success(request, 'File uploaded and extracted')

        return redirect(reverseContentUrl(self.folderAndPath))

    def _handleFileUpload(self, f):
        fileName = os.path.join(self.folderAndPath.absPath, f.name)
        dest = open(fileName, 'wb')

        for chunk in f.chunks():
            dest.write(chunk)

        dest.close()
        return fileName

    def _handleZipUpload(self, f):
        fileName = self._handleFileUpload(f)
        zipFile = ZipFile(fileName, mode='r')
        entries = zipFile.infolist()

        for entry in entries:
            zipFile.extract(entry, self.folderAndPath.absPath)

        zipFile.close()

        os.remove(fileName)


def getIndexIntoCurrentDir(request, folderAndPath, fileName):
    viewType = request.session.get('viewType', const.viewTypes[0])
    currentDirEntries = getCurrentDirEntries(folderAndPath, isShowHidden(request), viewType)

    for i in range(len(currentDirEntries)):
        if currentDirEntries[i].name == fileName:
            index = i
            result = {'currentDirEntries': currentDirEntries,
                      'index': i}
            return result


class ImageView(BaseContentView):
    def get(self, request, folderAndPathUrl, fileName, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)

        entries = getIndexIntoCurrentDir(request, self.folderAndPath, fileName)
        index = entries['index']
        currentDirEntries = entries['currentDirEntries']

        if index == 0:
            prevLink = None
        else:
            prevLink = reverseContentUrl(self.folderAndPath, viewName='imageView', extraPath=currentDirEntries[index-1].name)

        if index == len(currentDirEntries) - 1:
            nextLink = None
        else:
            nextLink = reverseContentUrl(self.folderAndPath, viewName='imageView', extraPath=currentDirEntries[index+1].name)

        parentDirLink = reverseContentUrl(self.folderAndPath)
        imageUrl = reverseContentUrl(self.folderAndPath, viewName='download%sImage' % self.folderAndPath.folder.name, extraPath=fileName)

        self.context['viewTypes'] = const.viewTypes
        self.context['parentDirLink'] = parentDirLink
        self.context['prevLink'] = prevLink
        self.context['nextLink'] = nextLink
        self.context['imageUrl'] = imageUrl
        self.context['fileName'] = fileName
        self.context['userCanDelete'] = self.userCanDelete

        return render(request, 'image_view.html', self.context)


class DeleteImageView(BaseContentView):
    def __init__(self):
        super(DeleteImageView, self).__init__(requireDelete=True)

    def post(self, request, folderAndPathUrl, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)
        fileName = request.POST['fileName']

        handleDelete(self.folderAndPath, [fileName])
        messages.success(request, 'File deleted')

        return redirect(reverseContentUrl(self.folderAndPath))


class GetNextImageView(BaseContentView):
    def get(self, request, folderAndPathUrl, fileName, *args, **kwargs):
        self._setup(request, folderAndPathUrl=folderAndPathUrl, *args, **kwargs)

        result = {}
        entries = getIndexIntoCurrentDir(request, self.folderAndPath, fileName)
        if entries:
            index = entries['index']
            currentDirEntries = entries['currentDirEntries']

            result['hasNextImage'] = False

            for i in range(index+1, len(currentDirEntries)):
                if imageRegex.match(currentDirEntries[i].name):
                    result['hasNextImage'] = True
                    nextFileName = currentDirEntries[i].name

                    imageUrl = reverseContentUrl(self.folderAndPath, viewName='download%sImage' % self.folderAndPath.folder.name, extraPath=nextFileName)
                    imageUrl = imageUrl.replace('//', '/')
                    result['imageUrl'] = imageUrl
                    result['fileName'] = nextFileName
                    break

        data = json.dumps(result)
        return HttpResponse(data, content_type='application/json')
