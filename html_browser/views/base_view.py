from django.shortcuts import redirect, render
from django.template import RequestContext
from html_browser.models import Folder
from django.contrib.auth import login as auth_login, logout as auth_logout
import html_browser
from html_browser.utils import getCurrentDirEntries, getCurrentDirEntriesSearch, handleDelete,\
    getPath, handleDownloadZip,\
    handleFileUpload, handleZipUpload,\
    getRequestField, getReqLogger
from html_browser.constants import _constants as const
from django.contrib.auth import authenticate
from sendfile import sendfile
import os
import re
import json
from django.http import HttpResponse
from django.views import View
import logging
from logging import DEBUG
import HTMLParser

logger = logging.getLogger(__name__)
imageRegex = re.compile("^([a-z])+.*\.(jpg|png|gif|bmp|avi)$",re.IGNORECASE)

class BaseView(View):
    def __init__(self):
        self.reqLogger = getReqLogger()
        self.folder = None
        self.currentFolder = None
        self.currentPath = None
        
    def get(self, request, *args, **kwargs):
        self.__commonGetPost(request)
    def post(self, request, *args, **kwargs):
        self.__commonGetPost(request)

    def __commonGetPost(self, request):
        self.reqLogger.info(self.__class__.__name__)
        if self.reqLogger.isEnabledFor(DEBUG):
            self.reqLogger.debug(str(request))

        self.currentFolder = getRequestField(self.request,'currentFolder')
        if self.currentFolder:
            h = HTMLParser.HTMLParser()
            self.currentPath = h.unescape(getRequestField(self.request,'currentPath'))
            self.folder = Folder.objects.filter(name=self.currentFolder)[0]

        self.context = {'user' : request.user,
                        'const': const
        }

        errorText = getRequestField(request, 'errorText')

        if errorText:
            self.context['errorText'] = errorText

        if self.currentFolder:
           self.context['currentFolder'] = self.currentFolder

        if self.currentPath:
           self.context['currentPath'] = self.currentPath

    @staticmethod
    def isShowHidden(request):
        if request.session.has_key('showHidden'):
            return request.session['showHidden']
        else:
            return False


class IndexView(BaseView):
    def get(self, request, *args, **kwargs):
        super(IndexView, self).get(request, args, kwargs)

        allFolders = Folder.objects.all()
        folders = []
        for folder in allFolders:
            if folder.userCanRead(request.user):
                folders.append(folder)
            
        self.context['folders'] = folders
    
        return render(request, 'index.html', self.context)

class LoginView(BaseView):
    def post(self, request, *args, **kwargs):
        super(LoginView, self).post(request, args, kwargs)

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
            self.reqLogger.error("empty userName")
    
        redirectUrl = const.BASE_URL

        if errorText != None:
            redirectUrl = "%s?errorText=%s" % (redirectUrl, errorText)
        return redirect(redirectUrl)


class LogoutView(BaseView):
    def get(self, request, *args, **kwargs):
        super(LogoutView, self).get(request, args, kwargs)
        auth_logout(request)
        return redirect(const.BASE_URL)

class DownloadView(BaseView):
    def get(self, request, *args, **kwargs):
        super(DownloadView, self).get(request, args, kwargs)

        fileName = request.GET['fileName']
    
        filePath = "/".join([self.folder.localPath + self.currentPath, fileName])
    
        return sendfile(request, filePath, attachment=True)

class DownloadZipView(BaseView):
    def get(self, request, *args, **kwargs):
        super(DownloadZipView, self).get(request, args, kwargs)
        return handleDownloadZip(request)

class UploadView(BaseView):
    def get(self, request, *args, **kwargs):
        super(UploadView, self).get(request, args, kwargs)

        userCanWrite = self.folder.userCanWrite(request.user)
    
        if not userCanWrite:
            return HttpResponse("You don't have write permission on this folder")
    
        self.context['status'] = ''
        self.context['viewTypes'] = const.viewTypes
    
        return render(request, 'upload.html', self.context)

class UploadActionView(BaseView):
    def post(self, request, *args, **kwargs):
        super(UploadActionView, self).post(request, args, kwargs)

        userCanWrite = self.folder.userCanWrite(request.user)
    
        if not userCanWrite:
            return HttpResponse("You don't have write permission on this folder")
    
        action = request.POST['action']
        if action == 'uploadFile':
            handleFileUpload(request.FILES['upload1'], self.folder, self.currentPath)
            redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=File uploaded" % (const.CONTENT_URL, self.currentFolder, self.currentPath)
            return redirect(redirectUrl)           
        elif action == 'uploadZip':
            handleZipUpload(request.FILES['zipupload1'], self.folder, self.currentPath)
            redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=File uploaded and extracted" % (const.CONTENT_URL, self.currentFolder, self.currentPath)
            return redirect(redirectUrl)         

def getIndexIntoCurrentDir(request, currentFolder, currentPath, fileName):
    folder = Folder.objects.filter(name=currentFolder)[0]
    userCanRead = folder.userCanRead(request.user)
    
    if not userCanRead:
        return HttpResponse("You don't have read permission on this folder")
    
    currentDirEntries = getCurrentDirEntries(folder, currentPath, BaseView.isShowHidden(request))
    
    for i in range(len(currentDirEntries)):
        if currentDirEntries[i].name == fileName:
            index = i
            result = {'currentDirEntries' : currentDirEntries,
                'index' : i}
            return result
        

class ImageView(BaseView):
    def get(self, request, *args, **kwargs):
        super(ImageView, self).get(request, args, kwargs)

        fileName = getRequestField(request,'fileName')
        entries = getIndexIntoCurrentDir(request, self.currentFolder, self.currentPath, fileName)
        index = entries['index']
        currentDirEntries = entries['currentDirEntries']

        if index == 0:
            prevLink = None
        else:
            prevLink = "%s?currentFolder=%s&currentPath=%s&fileName=%s" %(const.IMAGE_VIEW_URL, self.currentFolder, self.currentPath, currentDirEntries[index-1].name)
        
        if index == len(currentDirEntries) - 1:
            nextLink = None
        else:
            nextLink = "%s?currentFolder=%s&currentPath=%s&fileName=%s" %(const.IMAGE_VIEW_URL, self.currentFolder, self.currentPath, currentDirEntries[index+1].name)
        
        parentDirLink = "%s?currentFolder=%s&currentPath=%s" %(const.CONTENT_URL, self.currentFolder, self.currentPath)
    
        imageUrl = '%s__%s__%s/%s' %(const.BASE_URL, self.currentFolder, self.currentPath, fileName)
        imageUrl = imageUrl.replace('//','/')

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
        
class ThumbView(BaseView):
    def get(self, request, *args, **kwargs):
        super(ThumbView, self).get(request, args, kwargs)
        return render(request, 'test_image.html')

class DeleteImageView(BaseView):
    def get(self, request, *args, **kwargs):
        super(DeleteImageView, self).get(request, args, kwargs)

        userCanDelete = self.folder.userCanDelete(request.user)
    
        if not userCanDelete:
            status = "You don't have delete permission on this folder"
        else:
            handleDelete(self.folder, self.currentPath, getRequestField(request,'fileName'))
            status = "File deleted"

        redirectUrl = "%s?currentFolder=%s&currentPath=%s&status=%s" % (const.CONTENT_URL, self.currentFolder, self.currentPath, status)

        return redirect(redirectUrl)

class GetNextImageView(BaseView):
    def get(self, request, *args, **kwargs):
        super(GetNextImageView, self).get(request, args, kwargs)

        fileName = getRequestField(request,'fileName')

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

                    imageUrl = '%s__%s__%s/%s' %(const.BASE_URL, self.currentFolder, self.currentPath, nextFileName)
                    imageUrl = imageUrl.replace('//','/')
                    result['imageUrl'] = imageUrl
                    result['fileName'] = nextFileName
                    break;

        data = json.dumps(result)
        return HttpResponse(data, content_type='application/json')
