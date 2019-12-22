import collections
import json
import logging
import os
from datetime import datetime, timedelta
from shutil import copy2, copytree, move

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse

from html_browser._os import join_paths
from html_browser.constants import _constants as const
from html_browser.models import FilesToDelete
from html_browser.utils import (FolderAndPath, format_bytes, get_bytes_unit,
                                get_checked_entries, get_current_dir_entries,
                                handle_delete, replace_escaped_url)

from .base_view import BaseContentView, is_show_hidden, reverse_content_url

logger = logging.getLogger('html_browser.content_view')

_viewTypeToTemplateMap = {
    const.details_view_type: 'content_detail.html',
    const.list_view_type: 'content_list.html',
    const.thumbnails_view_type: 'content_thumbnail.html',
}

numItemsPerPage = 48


class ContentView(BaseContentView):
    def post(self, request, folder_and_path_url):
        action = request.POST['action']
        if action == 'copyToClipboard':
            entries = get_checked_entries(request.POST)
            request.session['clipboard'] = Clipboard(self.folder_and_path, entries, 'COPY').to_json()
            messages.success(request, 'Items copied to clipboard')
        elif action == 'cutToClipboard':
            if not self.user_can_delete:
                messages.error(request, "You don't have delete permission on this folder")
            else:
                entries = get_checked_entries(request.POST)
                request.session['clipboard'] = Clipboard(self.folder_and_path, entries, 'CUT').to_json()
                messages.success(request, 'Items copied to clipboard')
        elif action == 'pasteFromClipboard':
            if not self.user_can_write:
                messages.error(request, "You don't have write permission on this folder")
            else:
                self.__handlePaste(Clipboard.from_json(request.session['clipboard']))
        elif action == 'deleteEntry':
            if not self.user_can_delete:
                messages.error(request, "You don't have delete permission on this folder")
            else:
                handle_delete(self.folder_and_path, get_checked_entries(request.POST))
                messages.success(request, 'File(s) deleted')
        elif action == 'setViewType':
            view_type = request.POST['view_type']
            request.session['view_type'] = view_type
        elif action == 'mkDir':
            dirName = request.POST['dir']
            os.makedirs(join_paths(self.folder_and_path.abs_path, dirName))
        elif action == 'rename':
            self.handleRename(request.POST['file'], request.POST['newName'])
        elif action == 'changeSettings':
            if request.POST['submit'] == "Save":
                request.session['show_hidden'] = request.POST['show_hidden'] is not None
        else:
            raise RuntimeError('Unknown action %s' % action)

        return redirect(reverse_content_url(self.folder_and_path))

    def handleRename(self, file_name, newName):
        source = join_paths(self.folder_and_path.abs_path, replace_escaped_url(file_name))
        dest = join_paths(self.folder_and_path.abs_path, replace_escaped_url(newName))
        move(source, dest)

    def __handlePaste(self, clipboard):
        dest = self.folder_and_path.abs_path

        for entry in clipboard.entries:
            if os.path.exists(join_paths(dest, entry)):
                messages.error("One or more of the items already exists in the destination")
                return

        for entry in clipboard.entries:
            source = join_paths(clipboard.folder_and_path.abs_path, replace_escaped_url(entry))
            if clipboard.clipboardType == 'COPY':
                if os.path.isdir(source):
                    copytree(source, dest + entry)
                else:
                    copy2(source, dest)
            elif clipboard.clipboardType == 'CUT':
                move(source, dest)
            else:
                raise CopyPasteException()

        messages.success(self.request, 'Items pasted')

    def get(self, request, folder_and_path_url):
        ContentView.deleteOldFiles()

        self.breadcrumbs = None
        crumbs = self.folder_and_path.relative_path.split("/")
        if len(crumbs) >= 1:
            self.breadcrumbs = "<a href=\"%s\">Home</a> " % reverse('index')
            reverse_url = reverse_content_url(FolderAndPath(folder=self.folder_and_path.folder, path=''))
            self.breadcrumbs += "&rsaquo; <a href=\"%s\">%s</a> " % (reverse_url,
                                                                     self.folder_and_path.folder.name)

            accumulated = ""
            while len(crumbs) > 0:
                crumb = crumbs.pop(0)
                if crumb:
                    accumulated = "/".join([accumulated, crumb])
                    self.breadcrumbs = self.breadcrumbs + "&rsaquo; "
                    if len(crumbs) > 0:
                        url = reverse_content_url(FolderAndPath(folder=self.folder_and_path.folder, path=accumulated))
                        self.breadcrumbs += "<a href=\"{!s}\">{!s}</a> ".format(url, crumb)

                    else:
                        self.breadcrumbs = self.breadcrumbs + crumb

        content_filter = None
        if 'filter' in request.GET:
            content_filter = request.GET['filter']
            messages.info(request, 'Filtered on %s' % content_filter)

        self.context['user_can_read'] = str(self.user_can_read).lower()
        self.context['user_can_write'] = str(self.user_can_write).lower()
        self.context['user_can_delete'] = str(self.user_can_delete).lower()
        self.context['breadcrumbs'] = self.breadcrumbs
        self.context['show_hidden'] = is_show_hidden(request)

#        if 'search' in request.GET:
#            search = request.GET['search']
#            return self._handleSearch(request, search)

        view_type = request.session.get('view_type', const.view_types[0])
        current_dir_entries = get_current_dir_entries(self.folder_and_path, is_show_hidden(request), view_type, content_filter)

        if len(current_dir_entries) > numItemsPerPage and view_type == const.thumbnails_view_type:
            self.context['paginate'] = True
            paginator = Paginator(current_dir_entries, numItemsPerPage)
            page = request.GET.get('page', 1)
            current_dir_entries = paginator.get_page(page)
        else:
            self.context['paginate'] = False
        diskFreePct = getDiskPercentFree(self.folder_and_path.abs_path)
        diskUsage = getDiskUsageFormatted(self.folder_and_path.abs_path)

        parent_dir_link = getParentDirLink(self.folder_and_path)
        self.context['parent_dir_link'] = parent_dir_link
        self.context['view_type'] = const.view_types
        self.context['selectedViewType'] = view_type
        self.context['current_dir_entries'] = current_dir_entries
        self.context['diskFreePct'] = diskFreePct
        self.context['diskFree'] = diskUsage.freeformatted
        self.context['diskUsed'] = diskUsage.usedformatted
        self.context['diskTotal'] = diskUsage.totalformatted
        self.context['diskUnit'] = diskUsage.unit

        template = _viewTypeToTemplateMap[view_type]
        return render(request, template, self.context)

#    def _handleSearch(self, request, search):
#        current_dir_entries= get_current_dir_entries(self.folder, self.currentPath, BaseView.is_show_hidden(request), search)

#        self.context['current_dir_entries'] = current_dir_entries

#        return render(request, "content_search.html", self.context)

    @staticmethod
    def deleteOldFiles():
        now = datetime.now()
        for fileToDelete in FilesToDelete.objects.all().order_by('time'):
            delta = now - fileToDelete.time
            if delta > timedelta(minutes=10):
                if os.path.isfile(fileToDelete.file_path):
                    os.remove(fileToDelete.file_path)
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

    unit = get_bytes_unit(du.total)
    total = format_bytes(du.total, unit, False)
    used = format_bytes(du.used, unit, False)
    free = format_bytes(du.free, unit, False)

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


def getParentDirLink(folder_and_path):
    path = folder_and_path.relative_path
    if path:
        path = os.path.dirname(path)
        return reverse_content_url(FolderAndPath(folder_name=folder_and_path.folder.name, path=path))

    return reverse('index')


class Clipboard():
    def __init__(self, folder_and_path, entries, clipboardType):
        self.folder_and_path = folder_and_path
        self.clipboardType = clipboardType
        self.entries = entries

    @staticmethod
    def from_json(jsonStr):
        dictData = json.loads(jsonStr)
        return Clipboard(FolderAndPath.from_json(dictData['folder_and_path']), dictData['entries'], dictData['clipboardType'])

    def to_json(self):
        result = {'folder_and_path': self.folder_and_path.to_json(),
                  'clipboardType': self.clipboardType,
                  'entries': self.entries}

        return json.dumps(result)


class CopyPasteException(Exception):
    pass
