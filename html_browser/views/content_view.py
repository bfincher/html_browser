from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timedelta
from shutil import copy2, copytree, move
from typing import Callable, Dict, List, NamedTuple, Union

from django.contrib import messages
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import HttpResponsePermanentRedirect, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from html_browser._os import join_paths
from html_browser.constants import _constants as const
from html_browser.models import FilesToDelete
from html_browser.utils import (FolderAndPath, format_bytes, get_bytes_unit,
                                get_checked_entries,
                                handle_delete, replace_escaped_url)

from .base_view import BaseContentView, is_show_hidden, reverse_content_url

logger = logging.getLogger('html_browser.content_view')

_viewTypeToTemplateMap = {
    const.details_view_type: 'content_detail.html',
    const.list_view_type: 'content_list.html',
    const.thumbnails_view_type: 'content_thumbnail.html',
}

numItemsPerPage = 48


def _change_settings(request: HttpRequest) -> None:
    if request.POST['submit'] == "Save":
        request.session['show_hidden'] = request.POST['show_hidden'] is not None


def _set_view_type(request: HttpRequest) -> None:
    view_type = request.POST['view_type']
    request.session['view_type'] = view_type


class ContentView(BaseContentView): #pylint: disable=abstract-method

    def __init__(self) -> None:
        super().__init__()
        self.actionDict: Dict[str, Callable[[HttpRequest], None]] = {
            'copyToClipboard': self._copy_to_clipboard,
            'cutToClipboard': self._cut_to_clipboard,
            'pasteFromClipboard': self._paste_from_clipboard,
            'deleteEntry': self._delete_entry,
            'setViewType': _set_view_type,
            'mkDir': self._mkdir,
            'rename': self._rename,
            'changeSettings': _change_settings
        }
        self.breadcrumbs: str

    # folder_and_path_url is a required argument per urls.py.  This argument is consumed and processed
    # by the parent dispatch method
    def post(self,
             request: HttpRequest,
             folder_and_path_url: str) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect]: #pylint: disable=unused-argument

        action = request.POST['action']
        if action in self.actionDict:
            self.actionDict[action](request)
        else:
            raise RuntimeError(f'Unknown action {action}')

        return redirect(reverse_content_url(self.folder_and_path))

    def handleRename(self, file_name: str, new_name: str) -> None:
        source = join_paths(self.folder_and_path.abs_path, replace_escaped_url(file_name))
        dest = join_paths(self.folder_and_path.abs_path, replace_escaped_url(new_name))
        move(source, dest)

    def __handlePaste(self, request: HttpRequest) -> None:
        dest = self.folder_and_path.abs_path
        clipboard = Clipboard.from_json(request.session['clipboard'])

        for entry in clipboard.entries:
            if os.path.exists(join_paths(dest, entry)):
                messages.error(request, "One or more of the items already exists in the destination") #pylint: disable=no-value-for-parameter
                return

        for entry in clipboard.entries:
            source = join_paths(clipboard.folder_and_path.abs_path, replace_escaped_url(entry))
            if clipboard.type == 'COPY':
                if os.path.isdir(source):
                    copytree(source, dest + entry)
                else:
                    copy2(source, dest)
            elif clipboard.type == 'CUT':
                move(source, dest)
            else:
                raise CopyPasteException()

        messages.success(self.request, 'Items pasted')

    # folder_and_path_url is a required argument per urls.py.  This argument is consumed and processed
    # by the parent dispatch method
    def get(self, request: HttpRequest, folder_and_path_url: str) -> HttpResponse:  #pylint: disable=unused-argument
        ContentView.deleteOldFiles()
        self._build_breadcrumbs()

        content_filter = None
        if 'filter' in request.GET:
            content_filter = request.GET['filter']
            messages.info(request, f'Filtered on {content_filter}')

        self.context['user_can_read'] = str(self.user_can_read).lower()
        self.context['user_can_write'] = str(self.user_can_write).lower()
        self.context['user_can_delete'] = str(self.user_can_delete).lower()
        self.context['breadcrumbs'] = self.breadcrumbs
        self.context['show_hidden'] = is_show_hidden(request)

#        if 'search' in request.GET:
#            search = request.GET['search']
#            return self._handleSearch(request, search)

        view_type = request.session.get('view_type', const.view_types[0])
        current_dir_entries = self.folder_and_path.get_dir_entries(is_show_hidden(request), view_type, content_filter)

        if len(current_dir_entries) > numItemsPerPage and view_type == const.thumbnails_view_type:
            self.context['paginate'] = True
            paginator = Paginator(current_dir_entries, numItemsPerPage)
            page = request.GET.get('page', 1)
            current_dir_entries = paginator.get_page(page) #type: ignore
        else:
            self.context['paginate'] = False
        disk_usage = _get_disk_usage_formatted(self.folder_and_path.abs_path)

        self.context['parent_dir_link'] = get_parent_dir_link(self.folder_and_path)
        self.context['view_types'] = const.view_types
        self.context['selectedViewType'] = view_type
        self.context['current_dir_entries'] = current_dir_entries
        self.context['disk_free_pct'] = _get_disk_percent_free(self.folder_and_path.abs_path)
        self.context['diskFree'] = disk_usage.freeformatted
        self.context['diskUsed'] = disk_usage.usedformatted
        self.context['diskTotal'] = disk_usage.totalformatted
        self.context['diskUnit'] = disk_usage.unit

        template = _viewTypeToTemplateMap[view_type]
        return render(request, template, self.context)

#    def _handleSearch(self, request, search):
#        current_dir_entries= get_current_dir_entries(self.folder, self.currentPath, BaseView.is_show_hidden(request), search)

#        self.context['current_dir_entries'] = current_dir_entries

#        return render(request, "content_search.html", self.context)

    @staticmethod
    def deleteOldFiles() -> None:
        now = datetime.now()
        for file_to_delete in FilesToDelete.objects.all().order_by('time'):
            delta = now - file_to_delete.time
            if delta > timedelta(minutes=10):
                if os.path.isfile(file_to_delete.file_path):
                    os.remove(file_to_delete.file_path)
                file_to_delete.delete()
            else:
                return

    def _copy_to_clipboard(self, request: HttpRequest) -> None:
        entries = get_checked_entries(request.POST)
        request.session['clipboard'] = Clipboard(self.folder_and_path, entries, 'COPY').to_json()
        messages.success(request, 'Items copied to clipboard')

    def _cut_to_clipboard(self, request: HttpRequest) -> None:
        if not self.user_can_delete:
            messages.error(request, "You don't have delete permission on this folder")
        else:
            entries = get_checked_entries(request.POST)
            request.session['clipboard'] = Clipboard(self.folder_and_path, entries, 'CUT').to_json()
            messages.success(request, 'Items copied to clipboard')

    def _paste_from_clipboard(self, request: HttpRequest) -> None:
        if not self.user_can_write:
            messages.error(request, "You don't have write permission on this folder")
        else:
            self.__handlePaste(request)

    def _delete_entry(self, request: HttpRequest) -> None:
        if not self.user_can_delete:
            messages.error(request, "You don't have delete permission on this folder")
        else:
            handle_delete(self.folder_and_path, get_checked_entries(request.POST))
            messages.success(request, 'File(s) deleted')

    def _mkdir(self, request: HttpRequest) -> None:
        dir_name = request.POST['dir']
        os.makedirs(join_paths(self.folder_and_path.abs_path, dir_name))

    def _rename(self, request: HttpRequest) -> None:
        self.handleRename(request.POST['file'], request.POST['newName'])

    def _build_breadcrumbs(self) -> None:
        crumbs = self.folder_and_path.relative_path.split("/")
        if len(crumbs) >= 1:
            self.breadcrumbs = f"<a href=\"{reverse('index')}\">Home</a> "
            reverse_url = reverse_content_url(FolderAndPath(folder=self.folder_and_path.folder, path=''))
            self.breadcrumbs += f"&rsaquo; <a href=\"{reverse_url}\">{self.folder_and_path.folder.name}</a> "

            accumulated = ""
            while len(crumbs) > 0:
                crumb = crumbs.pop(0)
                if crumb:
                    accumulated = "/".join([accumulated, crumb])
                    self.breadcrumbs = self.breadcrumbs + "&rsaquo; "
                    if len(crumbs) > 0:
                        url = reverse_content_url(FolderAndPath(folder=self.folder_and_path.folder, path=accumulated))
                        self.breadcrumbs += f"<a href=\"{url}\">{crumb}</a> "

                    else:
                        self.breadcrumbs = self.breadcrumbs + crumb


def _get_disk_percent_free(path: str) -> str:
    du = _get_disk_usage(path)
    free = du.free / 1.0
    total = du.free + du.used / 1.0
    pct = free / total
    return f"{pct:.2%}"


class _Usage(NamedTuple):
    total: int
    used: int
    free: int


class _UsageFormatted(NamedTuple):
    total: int
    used: int
    free: int
    totalformatted: str
    usedformatted: str
    freeformatted: str
    unit: str


def _get_disk_usage_formatted(path: str) -> _UsageFormatted:
    du = _get_disk_usage(path)

    unit = get_bytes_unit(du.total)
    total = format_bytes(du.total, unit, False)
    used = format_bytes(du.used, unit, False)
    free = format_bytes(du.free, unit, False)

    return _UsageFormatted(total=du.total, totalformatted=total, used=du.used, usedformatted=used, free=du.free, freeformatted=free, unit=unit)


def _get_disk_usage(path: str) -> _Usage:

    if hasattr(os, 'statvfs'):  # POSIX
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return _Usage(total, used, free)

    if os.name == 'nt':  # Windows
        import ctypes #pylint: disable=import-outside-toplevel
        import sys    #pylint: disable=import-outside-toplevel

        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong() # type: ignore
        if sys.version_info >= (3,) or isinstance(path, str):
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW # type: ignore
        else:
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA # type: ignore
        ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free)) # type: ignore
        if ret == 0:
            raise ctypes.WinError() # type: ignore
        used = total.value - free.value # type: ignore
        return _Usage(total.value, used, free.value) # type: ignore

    raise NotImplementedError("platform not supported")


def get_parent_dir_link(folder_and_path: FolderAndPath) -> str:
    path = folder_and_path.relative_path
    if path:
        path = os.path.dirname(path)
        return reverse_content_url(FolderAndPath(folder_name=folder_and_path.folder.name, path=path))

    return reverse('index')


class Clipboard():

    def __init__(self, folder_and_path: FolderAndPath, entries: List[str], clipboardType: str) -> None:
        self.folder_and_path = folder_and_path
        self.type = clipboardType
        self.entries = entries

    @staticmethod
    def from_json(json_str):
        dict_data = json.loads(json_str)
        return Clipboard(FolderAndPath.from_json(dict_data['folder_and_path']), dict_data['entries'], dict_data['type'])

    def to_json(self) -> str:
        result = {'folder_and_path': self.folder_and_path.to_json(),
                  'type': self.type,
                  'entries': self.entries}

        return json.dumps(result)


class CopyPasteException(Exception):
    pass
