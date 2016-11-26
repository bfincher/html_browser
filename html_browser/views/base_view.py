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
    getPath,\
    handleFileUpload, handleZipUpload,\
    getRequestField, getReqLogger,\
    getCheckedEntries, replaceEscapedUrl

import json
import logging
from logging import DEBUG
import os
from pathlib import Path
import re
from sendfile import sendfile
import tempfile
from urllib.parse import quote_plus, unquote_plus
import zipfile
from zipfile import ZipFile

logger = logging.getLogger('html_browser.base_view')
imageRegex = re.compile("^([a-z])+.*\.(jpg|png|gif|bmp|avi)$", re.IGNORECASE)


def isShowHidden(request):
    return request.session.get('showHidden', False)


def reverseContentUrl(currentFolder, currentPath, viewName='content'):
    if currentPath:
        return reverse(viewName, kwargs={'currentFolder': currentFolder, 'currentPath': currentPath})
    else:
        return reverse(viewName, kwargs={'currentFolder': currentFolder})


class BaseView(View):
    def __init__(self):
        self.reqLogger = getReqLogger()

    def get(self, request, *args, **kwargs):
        self._commonGetPost(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._commonGetPost(request, *args, **kwargs)

    def _commonGetPost(self, request, *args, **kwargs):
        self.reqLogger.info(self.__class__.__name__)
        if self.reqLogger.isEnabledFor(DEBUG):
            _dict = None
            if request.method == "GET":
                _dict = request.GET
            else:
                _dict = request.POST

            if self.reqLogger.isEnabledFor(DEBUG):
                for key, value in sorted(_dict.items()):
                    if key in ['password', 'verifyPassword']:
                        self.reqLogger.debug("%s: ********", key)
                    else:
                        self.reqLogger.debug("%s: %s", key, value)

        self.context = {'user': request.user,
                        'const': const}


class BaseContentView(BaseView):
    def __init__(self, requireWrite=False, requireDelete=False):
        super(BaseContentView, self).__init__()
        self.folder = None
        self.currentFolder = None
        self.currentPath = ''
        self.requireWrite = requireWrite
        self.requireDelete = requireDelete

    def _commonGetPost(self, request, *args, **kwargs):
        super(BaseContentView, self)._commonGetPost(request, *args, **kwargs)

        self.currentFolder = kwargs['currentFolder']
        if self.currentFolder:
            self.currentPath = kwargs.get('currentPath', '')
            if self.currentPath:
                self.currentPath = unquote_plus(self.currentPath)
            self.folder = Folder.objects.filter(name=self.currentFolder)[0]

            if self.requireDelete and not self.folder.userCanDelete(request.user):
                raise PermissionDenied("Delete permission required")
            if self.requireWrite and not self.folder.userCanWrite(request.user):
                raise PermissionDenied("Write permission required")
            if not self.folder.userCanRead(request.user):
                raise PermissionDenied("Read permission required")

            self.context['currentFolder'] = self.currentFolder
            self.context['currentPath'] = self.currentPath


class IndexView(BaseView):
    def get(self, request, *args, **kwargs):
        super(IndexView, self).get(request, *args, **kwargs)

        allFolders = Folder.objects.all()
        folders = []
        for folder in allFolders:
            if folder.userCanRead(request.user):
                folders.append(folder)

        self.context['folders'] = folders

        return render(request, 'index.html', self.context)


class LoginView(BaseView):
    def post(self, request, *args, **kwargs):
        super(LoginView, self).post(request, *args, **kwargs)

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
        super(LogoutView, self).get(request, *args, **kwargs)
        auth_logout(request)
        return redirect('index')


class DownloadView(BaseContentView):
    def get(self, request, currentFolder, path, *args, **kwargs):
        super(DownloadView, self).get(request, currentFolder=currentFolder, currentPath=path, *args, **kwargs)
        path = unquote_plus(path)

        filePath = "/".join([self.folder.localPath,  path])

        return sendfile(request, filePath, attachment=True)


class DownloadImageView(BaseContentView):
    def get(self, request, currentFolder, path, *args, **kwargs):
        currentPath = os.path.dirname(path)
        super(DownloadImageView, self).get(request, currentFolder=currentFolder, currentPath=currentPath, *args, **kwargs)

        path = unquote_plus(path)

        imagePath = os.path.join(Folder.objects.get(name='Pictures').localPath, path)
        return sendfile(request, imagePath, attachment=False)


class DownloadZipView(BaseContentView):
    def get(self, request, currentFolder, currentPath, *args, **kwargs):
        super(DownloadZipView, self).get(request, currentFolder, currentPath, *args, **kwargs)

        compression = zipfile.ZIP_DEFLATED
        fileName = tempfile.mktemp(prefix="download_", suffix=".zip")
        self.zipFile = ZipFile(fileName, mode='w', compression=compression)

        self.basePath = getPath(self.folder.localPath, self.currentPath)
        for entry in getCheckedEntries(request.GET):
            path = getPath(self.folder.localPath, self.currentPath) + replaceEscapedUrl(entry)
            if os.path.isfile(path):
                self.__addFileToZip__(path)
            else:
                self.__addFolderToZip__(Path(path))

        self.zipFile.close()

        FilesToDelete.objects.create(filePath=fileName)

        return sendfile(request, fileName, attachment=True)

    def __addFileToZip__(self, fileToAdd):
        arcName = fileToAdd.replace(self.basePath, '')
        self.zipFile.write(fileToAdd, arcName, compress_type=zipfile.ZIP_DEFLATED)

    def __addFolderToZip__(self, folder):
        for f in folder.iterdir():
            if f.is_file():
                arcName = f.as_posix().replace(self.basePath, '')
                self.zipFile.write(f.as_posix(), arcName, compress_type=zipfile.ZIP_DEFLATED)
            elif f.is_dir():
                self.__addFolderToZip__(f)


class UploadView(BaseContentView):
    def __init__(self):
        super(UploadView, self).__init__(requireWrite=True)

    def get(self, request, currentFolder, currentPath, *args, **kwargs):
        super(UploadView, self).get(request, currentFolder, currentPath, *args, **kwargs)

        self.context['viewTypes'] = const.viewTypes

        return render(request, 'upload.html', self.context)

    def post(self, request, currentFolder, currentPath, *args, **kwargs):
        super(UploadView, self).post(request, currentFolder, currentPath, *args, **kwargs)

        action = request.POST['action']
        if action == 'uploadFile':
            handleFileUpload(request.FILES['upload1'], self.folder, self.currentPath)
            message.success(request, 'File uploaded')
        elif action == 'uploadZip':
            handleZipUpload(request.FILES['zipupload1'], self.folder, self.currentPath)
            message.success(request, 'File uploaded and extracted')

        return redirect('index')


def getIndexIntoCurrentDir(request, currentFolder, currentPath, fileName):
    folder = Folder.objects.filter(name=currentFolder)[0]
    currentDirEntries = getCurrentDirEntries(folder, currentPath, isShowHidden(request))

    for i in range(len(currentDirEntries)):
        if currentDirEntries[i].name == fileName:
            index = i
            result = {'currentDirEntries': currentDirEntries,
                      'index': i}
            return result


class ImageView(BaseContentView):
    def get(self, request, currentFolder, currentPath, *args, **kwargs):
        fileName = os.path.basename(currentPath)
        currentPath = os.path.dirname(currentPath)
        super(ImageView, self).get(request, currentFolder=currentFolder, currentPath=currentPath, *args, **kwargs)

        entries = getIndexIntoCurrentDir(request, self.currentFolder, self.currentPath, fileName)
        index = entries['index']
        currentDirEntries = entries['currentDirEntries']

        if index == 0:
            prevLink = None
        else:
            prevLink = reverseContentUrl(self.currentFolder, 
                                         self.currentPath + '/' + currentDirEntries[index-1].name,
                                         'imageView')

        if index == len(currentDirEntries) - 1:
            nextLink = None
        else:
            nextLink = reverseContentUrl(self.currentFolder,
                                         self.currentPath + "/" + currentDirEntries[index+1].name,
                                         'imageView')

        parentDirLink = reverseContentUrl(self.currentFolder, self.currentPath)

        imageUrl = reverse('download%sImage' % self.folder.name,
                           kwargs={'currentFolder': self.currentFolder,
                                   'path': '%s/%s' % (self.currentPath, fileName)})

        deleteImageUrl = reverse('deleteImage', kwargs={ 'currentFolder': self.currentFolder,
                                 'currentPath': self.currentPath})

        userCanDelete = self.folder.userCanDelete(request.user)

        self.context['viewTypes'] = const.viewTypes
        self.context['fileName'] = fileName
        self.context['parentDirLink'] = parentDirLink
        self.context['prevLink'] = prevLink
        self.context['nextLink'] = nextLink
        self.context['imageUrl'] = imageUrl
        self.context['fileName'] = fileName
        self.context['userCanDelete'] = userCanDelete
        self.context['deleteImageUrl'] = deleteImageUrl

        return render(request, 'image_view.html', self.context)


class ThumbView(BaseContentView):
    def get(self, request, currentFolder, currentPath, *args, **kwargs):
        super(ThumbView, self).get(request, currentFolder, currentPath, *args, **kwargs)
        return render(request, 'test_image.html')


class DeleteImageView(BaseContentView):
    def __init__(self):
        super(DeleteImageView, self).__init__(requireDelete=True)

    def post(self, request, currentFolder, currentPath, *args, **kwargs):
        super(DeleteImageView, self).post(request, currentFolder=currentFolder, currentPath=currentPath, *args, **kwargs)
        fileName = request.POST['fileName']

        handleDelete(self.folder, self.currentPath, [fileName])
        messages.success(request, 'File deleted')

        return redirect(reverseContentUrl(self.currentFolder, self.currentPath))


class GetNextImageView(BaseContentView):
    def get(self, request, currentFolder, path, *args, **kwargs):
        currentPath = os.path.dirname(path)
        fileName = os.path.basename(path)
        super(GetNextImageView, self).get(request, currentFolder=currentFolder, currentPath=currentPath, *args, **kwargs)

        result = {}
        entries = getIndexIntoCurrentDir(request, self.currentFolder, self.currentPath, fileName)
        if entries:
            index = entries['index']
            currentDirEntries = entries['currentDirEntries']

            result['hasNextImage'] = False

            for i in range(index+1, len(currentDirEntries)):
                if imageRegex.match(currentDirEntries[i].name):
                    result['hasNextImage'] = True
                    nextFileName = currentDirEntries[i].name

                    imageUrl = reverse('download%sImage' % self.folder.name,
                                       kwargs={'currentFolder': self.currentFolder,
                                               'path': self.currentPath + "/" + nextFileName})
                    imageUrl = imageUrl.replace('//', '/')
                    result['imageUrl'] = imageUrl
                    result['fileName'] = nextFileName
                    break

        data = json.dumps(result)
        return HttpResponse(data, content_type='application/json')
