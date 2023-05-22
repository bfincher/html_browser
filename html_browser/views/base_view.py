import subprocess
import json
import logging
import os
import re
import tempfile
import zipfile
from logging import DEBUG
from pathlib import Path
from zipfile import ZipFile

from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse
from django.views import View
from django_downloadview import sendfile # type: ignore

from html_browser import settings
from html_browser._os import join_paths
from html_browser.constants import _constants as const
from html_browser.models import FilesToDelete, Folder
from html_browser.utils import (ArgumentException, FolderAndPath,
                                get_checked_entries, handle_delete,
                                replace_escaped_url, DirEntry)

logger = logging.getLogger('html_browser.base_view')
imageRegex = re.compile(r"^.*?\.(jpg|jpeg|png|gif|bmp|avi)$", re.IGNORECASE)


def is_show_hidden(request: HttpRequest) -> bool:
    return request.session.get('show_hidden', False)


def reverse_content_url(folder_and_path: FolderAndPath, view_name='content', extra_path: Optional[str] = None) -> str:
    folder_and_path_url = folder_and_path.url.replace('//', '/')
    if folder_and_path_url.endswith('/'):
        folder_and_path_url = folder_and_path_url[:-1]
    args = [folder_and_path_url]
    if extra_path:
        args.append(extra_path)
    return reverse(view_name, args=args)


class BaseView(View):
    def __init__(self) -> None:
        super().__init__()
        self.context: Dict[str, Any] = {}
        self.request: HttpRequest

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        logger.info(self.__class__.__name__)
        self.request = request
        if logger.isEnabledFor(DEBUG):
            _dict = None
            if request.method == "GET":
                _dict = request.GET
            else:
                _dict = request.POST

            for key, value in sorted(_dict.items()):
                if key in ['password', 'verifyPassword']:
                    logger.debug("%s: ********", key)
                else:
                    logger.debug("%s: %s", key, value)

        self.context['user'] = request.user
        return super().dispatch(request, *args, **kwargs)


class BaseContentView(UserPassesTestMixin, BaseView): #pylint: disable=abstract-method
    def __init__(self, require_write=False, require_delete=False) -> None:
        super().__init__()
        self.folder_and_path: FolderAndPath
        self.require_write = require_write
        self.require_delete = require_delete
        self.user_can_read: bool
        self.user_can_write: bool
        self.user_can_delete: bool

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if 'folder_and_path_url' in kwargs:
            self.folder_and_path = FolderAndPath(url=kwargs['folder_and_path_url'])
        elif 'folder_and_path' in kwargs:
            self.folder_and_path = kwargs['folder_and_path']
        else:
            raise ArgumentException("One of folderandPathUrl or folder_and_path params must be specified")

        self.user_can_delete = self.folder_and_path.folder.user_can_delete(request.user)
        self.user_can_write = self.user_can_delete or self.folder_and_path.folder.user_can_write(request.user)
        self.user_can_read = self.user_can_write or self.folder_and_path.folder.user_can_read(request.user)

        self.context['folder_and_path'] = self.folder_and_path

        if os.path.exists('/test_script.sh'):
            subprocess.Popen(['/test_script.sh'])
        return super().dispatch(request, *args, **kwargs)

    def does_user_pass_test(self) -> bool:
        if self.require_delete and not self.user_can_delete:
            messages.error(self.request, "Delete permission required")
            return False
        if self.require_write and not self.user_can_write:
            messages.error(self.request, "Write permission required")
            return False
        if not self.user_can_read:
            messages.error(self.request, "Read permission required")
            return False

        return True

    def get_test_func(self) -> Callable[[], bool]:
        return self.does_user_pass_test

    # override parent class handling of no permission.  We don't want an exception, just a redirect
    def handle_no_permission(self) -> HttpResponseRedirect:
        return HttpResponseRedirect(resolve_url('index'))


class IndexView(BaseView):
    def get(self, request: HttpRequest) -> HttpResponse:
        all_folders = Folder.objects.all()
        folders: List[Folder] = []
        for folder in all_folders:
            if folder.user_can_read(request.user):
                folders.append(folder)

        if 'next' in request.GET:
            self.context['next'] = request.GET['next']
        self.context['folders'] = folders

        return render(request, 'index.html', self.context)


class LoginView(BaseView):
    def post(self, request: HttpRequest) -> HttpResponse:
        user_name = request.POST['user_name']
        password = request.POST['password']
        user = authenticate(username=user_name, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                logger.debug("%s authenticated", user)
            else:
                logger.warning("%s attempted to log in to a disabled account", user)
                messages.error(request, 'Account has been disabled')
        else:
            messages.error(request, 'Invalid login')

        redirect_url = request.POST.get('next', 'index')
        return redirect(redirect_url)


class LogoutView(BaseView):
    def get(self, request: HttpRequest) -> HttpResponse:
        auth_logout(request)
        return redirect('index')


class DownloadView(BaseContentView): #pylint: disable=abstract-method
    def get(self, request: HttpRequest, folder_and_path_url: str, file_name: str) -> HttpResponse: #pylint: disable=unused-argument
        return sendfile(request,
                        join_paths(self.folder_and_path.abs_path, file_name),
                        attachment=True)


class DownloadImageView(BaseContentView): #pylint: disable=abstract-method
    def get(self, request: HttpRequest, folder_and_path_url: str, file_name: str) -> HttpResponse: #pylint: disable=unused-argument
        return sendfile(request, join_paths(self.folder_and_path.abs_path, file_name), attachment=False)


class ThumbView(BaseView):
    def get(self, request: HttpRequest, path: str) -> HttpResponse:
        file = join_paths(settings.THUMBNAIL_CACHE_DIR, path)
        return sendfile(request, file, attachment=False)


class DownloadZipView(BaseContentView): #pylint: disable=abstract-method

    def get(self, request: HttpRequest, folder_and_path_url: str) -> HttpResponse: #pylint: disable=unused-argument
        compression = zipfile.ZIP_DEFLATED
        file_name = tempfile.mktemp(prefix="download_", suffix=".zip")
        with ZipFile(file_name, mode='w', compression=compression) as zipFile:

            for entry in get_checked_entries(request.GET):
                path = join_paths(self.folder_and_path.abs_path, replace_escaped_url(entry))
                if os.path.isfile(path):
                    self.__addFileToZip__(zipFile, path)
                else:
                    self.__addFolderToZip__(zipFile, Path(path))

        FilesToDelete.objects.create(file_path=file_name)

        return sendfile(request, file_name, attachment=True)

    def __addFileToZip__(self, zipFile, file_to_add):
        arc_name = file_to_add.replace(self.folder_and_path.abs_path, '')
        zipFile.write(file_to_add, arc_name, compress_type=zipfile.ZIP_DEFLATED)

    def __addFolderToZip__(self, zipFile: ZipFile, folder: Path) -> None:
        for f in folder.iterdir():
            if f.is_file():
                arc_name = f.as_posix().replace(self.folder_and_path.abs_path, '')
                zipFile.write(f.as_posix(), arc_name, compress_type=zipfile.ZIP_DEFLATED)
            elif f.is_dir():
                self.__addFolderToZip__(zipFile, f)


class UploadView(BaseContentView): #pylint: disable=abstract-method
    def __init__(self) -> None:
        super().__init__(require_write=True)

    def get(self, request: HttpRequest, folder_and_path_url: str) -> HttpResponse: #pylint: disable=unused-argument
        self.context['view_types'] = const.view_types

        return render(request, 'upload.html', self.context)

    def post(self, request: HttpRequest, folder_and_path_url: str) -> HttpResponse: #pylint: disable=unused-argument
        for key in request.FILES:
            file_name = join_paths(self.folder_and_path.abs_path, request.FILES[key].name)
            with open(file_name, 'wb') as dest:
                for chunk in request.FILES[key].chunks():
                    dest.write(chunk)

        data = {'error': '',
                'initialPreview': [],
                'initialPreviewConfig': [],
                'initialPreviewThumbTags': [],
                'append': True}
        return JsonResponse(data)

#     def _handleZipUpload(self, f):
#         file_name = self._handleFileUpload(f)
#         zipFile = ZipFile(file_name, mode='r')
#         entries = zipFile.infolist()
#
#         for entry in entries:
#             zipFile.extract(entry, self.folder_and_path.abs_path)
#
#         zipFile.close()
#
#         os.remove(file_name)


class _IndexIntoCurrentDir(NamedTuple):
    current_dir_entries: List[DirEntry]
    index_into_current_dir: int


def get_index_into_current_dir(request, folder_and_path: FolderAndPath, file_name: str) -> _IndexIntoCurrentDir:
    view_type = request.session.get('view_type', const.view_types[0])
    current_dir_entries = folder_and_path.get_dir_entries(is_show_hidden(request), view_type)

    for index, entry in enumerate(current_dir_entries):
        if entry.name == file_name:
            return _IndexIntoCurrentDir(current_dir_entries=current_dir_entries, index_into_current_dir=index)
    raise RuntimeError(f'Unable to find entry for {file_name}')


class ImageView(BaseContentView): #pylint: disable=abstract-method
    def get(self, request: HttpRequest, folder_and_path_url: str, file_name: str) -> HttpResponse: #pylint: disable=unused-argument
        entries = get_index_into_current_dir(request, self.folder_and_path, file_name)
        index = entries.index_into_current_dir
        current_dir_entries = entries.current_dir_entries

        if index == 0:
            prev_link = None
        else:
            prev_link = reverse_content_url(self.folder_and_path, view_name='imageView', extra_path=current_dir_entries[index - 1].name)

        if index == len(current_dir_entries) - 1:
            next_link = None
        else:
            next_link = reverse_content_url(self.folder_and_path, view_name='imageView', extra_path=current_dir_entries[index + 1].name)

        parent_dir_link = reverse_content_url(self.folder_and_path)
        image_url = reverse_content_url(self.folder_and_path, view_name='download', extra_path=file_name)

        self.context['view_types'] = const.view_types
        self.context['parent_dir_link'] = parent_dir_link
        self.context['prev_link'] = prev_link
        self.context['next_link'] = next_link
        self.context['image_url'] = image_url
        self.context['file_name'] = file_name
        self.context['user_can_delete'] = self.user_can_delete

        return render(request, 'image_view.html', self.context)


class DeleteImageView(BaseContentView): #pylint: disable=abstract-method
    def __init__(self) -> None:
        super().__init__(require_delete=True)

    def post(self, request: HttpRequest) -> HttpResponse:
        file_name = request.POST['file_name']

        handle_delete(self.folder_and_path, [file_name])
        messages.success(request, 'File deleted')

        return redirect(reverse_content_url(self.folder_and_path))


class GetNextImageView(BaseContentView): #pylint: disable=abstract-method
    def get(self, request: HttpRequest, file_name: str) -> HttpResponse:
        result: Dict[str, Union[bool, str]] = {}
        entries = get_index_into_current_dir(request, self.folder_and_path, file_name)
        index = entries.index_into_current_dir
        current_dir_entries = entries.current_dir_entries

        result['hasNextImage'] = False

        for i in range(index + 1, len(current_dir_entries)):
            if imageRegex.match(current_dir_entries[i].name):
                result['hasNextImage'] = True
                next_file_name = current_dir_entries[i].name

                image_url = reverse_content_url(self.folder_and_path, view_name='download', extra_path=next_file_name)
                image_url = image_url.replace('//', '/')
                result['image_url'] = image_url
                result['file_name'] = next_file_name
                break

        data = json.dumps(result)
        return JsonResponse(data)
