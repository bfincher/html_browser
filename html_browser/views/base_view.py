from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
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

from html.parser import HTMLParser
import json
import logging
from logging import DEBUG
import os
from pathlib import Path
import re
from sendfile import sendfile
import tempfile
import zipfile
from zipfile import ZipFile

logger = logging.getLogger('html_browser.base_view')
imageRegex = re.compile("^([a-z])+.*\.(jpg|png|gif|bmp|avi)$", re.IGNORECASE)


def isShowHidden(request):
    return request.session.get('showHidden', False)


class BaseView(View):
    def __init__(self):
        self.reqLogger = getReqLogger()
        self.errorHtml = ""

    def get(self, request, *args, **kwargs):
        self._commonGetPost(request)

    def post(self, request, *args, **kwargs):
        self._commonGetPost(request)

    def _commonGetPost(self, request):
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

        errorText = getRequestField(request, 'errorText')
        if errorText:
            self.context['errorText'] = errorText

        if self.errorHtml:
            self.context['errorHtml'] = self.errorHtml
        else:
            errorHtml = getRequestField(request, 'errorHtml')
            if errorHtml:
                self.context['errorHtml'] = errorHtml

    def redirect(self, url, *args, **kwargs):
        if url.startswith(const.BASE_URL):
            redirectUrl = url
        else:
            redirectUrl = reverse(url)

        separator = '?'
        for key, value in sorted(kwargs.items()):
            if value:
                redirectUrl += "%s%s=%s" % (separator, key, value)
                separator = '&'

        return redirect(redirectUrl)


class BaseContentView(BaseView):
    def __init__(self, requireWrite=False, requireDelete=False):
        super(BaseContentView, self).__init__()
        self.folder = None
        self.currentFolder = None
        self.currentPath = None
        self.requireWrite = requireWrite
        self.requireDelete = requireDelete

    def _commonGetPost(self, request):
        super(BaseContentView, self)._commonGetPost(request)

        self.currentFolder = getRequestField(self.request, 'currentFolder')
        if self.currentFolder:
            h = HTMLParser()
            self.currentPath = h.unescape(getRequestField(self.request, 'currentPath'))
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

        errorText = None

        user = authenticate(username=userName, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                if self.reqLogger.isEnabledFor(DEBUG):
                    self.reqLogger.debug("%s authenticated", user)
            else:
                self.reqLogger.warn("%s attempted to log in to a disabled account", user)
                errorText = 'Account has been disabled'
        else:
            errorText = 'Invalid login'

        return self.redirect('index', errorText=errorText)


class LogoutView(BaseView):
    def get(self, request, *args, **kwargs):
        super(LogoutView, self).get(request, *args, **kwargs)
        auth_logout(request)
        return redirect(const.BASE_URL)


class DownloadView(BaseContentView):
    def get(self, request, *args, **kwargs):
        super(DownloadView, self).get(request, *args, **kwargs)

        fileName = request.GET['fileName']

        filePath = "/".join([self.folder.localPath + self.currentPath, fileName])

        return sendfile(request, filePath, attachment=True)


class DownloadImageView(BaseContentView):
    def get(self, request, path, *args, **kwargs):
        super(DownloadImageView, self).get(request, *args, **kwargs)

        imagePath = os.path.join(Folder.objects.get(name='Pictures').localPath, path)
        return sendfile(request, imagePath, attachment=False)


class DownloadZipView(BaseContentView):
    def get(self, request, *args, **kwargs):
        super(DownloadZipView, self).get(request, *args, **kwargs)

        currentFolder = request.GET['currentFolder']
        currentPath = request.GET['currentPath']
        folder = Folder.objects.filter(name=currentFolder)[0]
        compression = zipfile.ZIP_DEFLATED
        fileName = tempfile.mktemp(prefix="download_", suffix=".zip")
        self.zipFile = ZipFile(fileName, mode='w', compression=compression)

        self.basePath = getPath(folder.localPath, currentPath)
        for entry in getCheckedEntries(request.GET):
            path = getPath(folder.localPath, currentPath) + replaceEscapedUrl(entry)
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

    def get(self, request, *args, **kwargs):
        super(UploadView, self).get(request, *args, **kwargs)

        self.context['status'] = ''
        self.context['viewTypes'] = const.viewTypes

        return render(request, 'upload.html', self.context)

    def post(self, request, *args, **kwargs):
        super(UploadView, self).post(request, *args, **kwargs)

        action = request.POST['action']
        status = None
        if action == 'uploadFile':
            handleFileUpload(request.FILES['upload1'], self.folder, self.currentPath)
            status = 'File uploaded'
        elif action == 'uploadZip':
            handleZipUpload(request.FILES['zipupload1'], self.folder, self.currentPath)
            status = 'File uploaded and extracted'

        return self.redirect(const.CONTENT_URL, currentFolder=self.currentFolder, currentPath=self.currentPath, status=status)


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
    def get(self, request, *args, **kwargs):
        super(ImageView, self).get(request, *args, **kwargs)

        fileName = request.GET['fileName']
        entries = getIndexIntoCurrentDir(request, self.currentFolder, self.currentPath, fileName)
        index = entries['index']
        currentDirEntries = entries['currentDirEntries']

        if index == 0:
            prevLink = None
        else:
            prevLink = "%s?currentFolder=%s&currentPath=%s&fileName=%s" %\
            (const.IMAGE_VIEW_URL, self.currentFolder, self.currentPath, currentDirEntries[index-1].name)

        if index == len(currentDirEntries) - 1:
            nextLink = None
        else:
            nextLink = "%s?currentFolder=%s&currentPath=%s&fileName=%s" %\
            (const.IMAGE_VIEW_URL, self.currentFolder, self.currentPath, currentDirEntries[index+1].name)

        parentDirLink = "%s?currentFolder=%s&currentPath=%s" % (const.CONTENT_URL, self.currentFolder, self.currentPath)

        imageUrl = '%s__%s__%s/%s' % (const.BASE_URL, self.currentFolder, self.currentPath, fileName)
        imageUrl = imageUrl.replace('//', '/')

        userCanDelete = self.folder.userCanDelete(request.user)

        self.context['status'] = ''
        self.context['viewTypes'] = const.viewTypes
        self.context['fileName'] = fileName
        self.context['parentDirLink'] = parentDirLink
        self.context['prevLink'] = prevLink
        self.context['nextLink'] = nextLink
        self.context['imageUrl'] = imageUrl
        self.context['fileName'] = fileName
        self.context['userCanDelete'] = userCanDelete

        return render(request, 'image_view.html', self.context)


class ThumbView(BaseContentView):
    def get(self, request, *args, **kwargs):
        super(ThumbView, self).get(request, *args, **kwargs)
        return render(request, 'test_image.html')


class DeleteImageView(BaseContentView):
    def __init__(self):
        super(DeleteImageView, self).__init__(requireDelete=True)

    def get(self, request, *args, **kwargs):
        super(DeleteImageView, self).get(request, *args, **kwargs)

        handleDelete(self.folder, self.currentPath, request.GET['fileName'])
        status = "File deleted"

        return self.redirect(const.CONTENT_URL, currentFolder=self.currentFolder, currentPath=self.currentPath, status=status)


class GetNextImageView(BaseContentView):
    def get(self, request, *args, **kwargs):
        super(GetNextImageView, self).get(request, *args, **kwargs)

        fileName = request.GET['fileName']

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

                    imageUrl = '%s__%s__%s/%s' % (const.BASE_URL, self.currentFolder, self.currentPath, nextFileName)
                    imageUrl = imageUrl.replace('//', '/')
                    result['imageUrl'] = imageUrl
                    result['fileName'] = nextFileName
                    break

        data = json.dumps(result)
        return HttpResponse(data, content_type='application/json')
