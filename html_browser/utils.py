from __future__ import annotations
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
from typing import List, Optional

from django.core.files.storage import FileSystemStorage
from django.shortcuts import _get_queryset # type: ignore
from django.urls import reverse
from sorl.thumbnail import get_thumbnail # type: ignore

from html_browser import settings
from html_browser._os import join_paths
from html_browser.models import Folder

from .constants import _constants as const

logger = logging.getLogger('html_browser.utils')

KILOBYTE = 1024.0
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = MEGABYTE * KILOBYTE
THUMBNAIL_GEOMETRY = '150x150'

checkBoxEntryRegex = re.compile(r'cb-(.+)')
folder_and_path_regex = re.compile(r'^(\w+)(/(.*))?$')
IMAGE_REGEX_STR = r'.+\.((jpg)|(jpeg)|(png)|(bmp))'
imageRegex = re.compile(fr'(?i){IMAGE_REGEX_STR}')
imageRegexWithCach = re.compile(fr'(?i)cache/{IMAGE_REGEX_STR}')


class ThumbnailStorage(FileSystemStorage):
    def __init__(self) -> None:
        path = Path(settings.THUMBNAIL_CACHE_DIR)
        if not path.exists():
            path.mkdir(parents=True)
        super().__init__(location=settings.THUMBNAIL_CACHE_DIR)

    def path(self, name: str) -> str:
        if imageRegexWithCach.match(name):
            return join_paths(self.base_location, name)
        return name


class NoParentException(Exception):
    pass


class ArgumentException(Exception):
    pass


class FolderAndPathArgumentException(Exception):
    def __init__(self, **kwargs) -> None:
        super().__init__(f"Expected kwargs are (url)|(folder_name, path).  Instead found {kwargs}")


class FolderAndPath: # pylint: disable=too-many-instance-attributes

    def __init__(self, **kwargs) -> None:
        # options for kwargs are (url)|(folder_name, path)

        self.relative_path = ''
        if 'url' in kwargs and len(kwargs) == 1:
            match = folder_and_path_regex.match(kwargs['url'])
            if match:
                folder_name = match.groups()[0]
                relative_path_match = match.groups()[2]
                if relative_path_match:
                    self.relative_path = unquote_plus(relative_path_match)

            self.folder = Folder.objects.get(name=folder_name)
            self.abs_path = join_paths(self.folder.local_path, self.relative_path)
            self.url = kwargs['url']
        elif 'path' in kwargs and len(kwargs) == 2:
            if 'folder_name' in kwargs:
                self.folder = Folder.objects.get(name=kwargs['folder_name'])
            elif 'folder' in kwargs:
                self.folder = kwargs['folder']
            else:
                raise FolderAndPathArgumentException(**kwargs)

            # just in case the path argument already has the folder localpath appended, try to replace the folder.localpath prefix
            self.relative_path = re.sub(fr'^{self.folder.local_path}', '', kwargs['path'])

            self.abs_path = join_paths(self.folder.local_path, self.relative_path)
            self.url = f"{self.folder.name}/{self.relative_path}"
        else:
            raise FolderAndPathArgumentException(**kwargs)

        self.dir_entries: List[DirEntry]
        self.file_entries: List[DirEntry]
        self.skip_thumbnail = False
        self.start_time: datetime

    def __str__(self) -> str:
        return f"folder_name = {self.folder.name}, relative_path = {self.relative_path}, abs_path = {self.abs_path}, url = {self.url}"

    def get_parent(self) -> FolderAndPath:
        if self.relative_path == '':
            raise NoParentException()

        return FolderAndPath(folder_name=self.folder.name, path=os.path.dirname(self.relative_path))

    @staticmethod
    def from_json(json_str) -> FolderAndPath:
        dict_data = json.loads(json_str)
        return FolderAndPath(**dict_data)

    def to_json(self) -> str:
        result = {'folder_name': self.folder.name,
                  'path': self.relative_path}
        return json.dumps(result)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FolderAndPath):
            return NotImplemented
        return self.url == other.url

    def get_dir_entries(self, show_hidden: bool, view_type: str, content_filter: Optional[str] = None) -> List[DirEntry]:
        _dir = self.abs_path
        if os.path.isfile(_dir):
            _dir = os.path.dirname(_dir)

        dir_entries: List[DirEntry] = []
        file_entries: List[DirEntry] = []
        self.dir_entries = dir_entries
        self.file_entries = file_entries

        self.skip_thumbnail = False
        self.start_time = datetime.now()

        if _dir.endswith('lost+found'):
            return []

        for file in Path(_dir).iterdir():
            self._process_entry(file, show_hidden, view_type, content_filter)

        dir_entries.sort(key=attrgetter('name'))
        file_entries.sort(key=attrgetter('name'))

        dir_entries.extend(file_entries)

        delattr(self, "skip_thumbnail")
        delattr(self, "start_time")
        delattr(self, "dir_entries")
        delattr(self, "file_entries")
        return dir_entries

    def _process_entry(self, entry: Path, show_hidden: bool, view_type: str, content_filter: Optional[str] = None) -> None:
        if not show_hidden and entry.name.startswith('.'):
            return
        try:
            if entry.is_dir():
                self.dir_entries.append(DirEntry(entry, self, view_type))
            else:
                include = False
                if content_filter:
                    temp_filter = content_filter.replace('.', r'\.')
                    temp_filter = temp_filter.replace('*', '.*')
                    if re.search(temp_filter, entry.name):
                        include = True
                else:
                    include = True

                delta = datetime.now() - self.start_time
                skip_thumbnail = self.skip_thumbnail or delta.total_seconds() > 45
                if include:
                    self.file_entries.append(DirEntry(entry, self, view_type, skip_thumbnail))
        except (OSError, UnicodeDecodeError) as exception:
            logger.exception(exception)


def get_checked_entries(request_dict) -> List[str]:
    entries = []
    for key in request_dict:
        match = checkBoxEntryRegex.match(key)
        if match and request_dict[key] == 'on':
            entries.append(match.group(1))

    return entries


class DirEntry(): # pylint: disable=too-many-instance-attributes

    def __init__(self, path: Path, folder_and_path: FolderAndPath, view_type: str, skip_thumbnail=False) -> None:
        self.thumbnail_url = None # type: Optional[str]
        self.is_dir = path.is_dir()
        self.name = path.name
        self.name_url = self.name.replace('&', '&amp;')
        self.name_url = quote_plus(self.name)

        stat = path.stat()
        if self.is_dir:
            self.size = '&nbsp'
        else:
            size = stat.st_size
            self.size = format_bytes(size)
            self.size_numeric = size

        last_modify_time = datetime.fromtimestamp(stat.st_mtime)
        self.last_modify_time = last_modify_time.strftime('%Y-%m-%d %I:%M:%S %p')

        if not skip_thumbnail and not self.is_dir and view_type == const.thumbnails_view_type and imageRegex.match(self.name):
            self.has_thumbnail = True
            self.image_link_path = join_paths(folder_and_path.folder.local_path, folder_and_path.relative_path, self.name)

            # make call to get thumbnail url here so that the createthumbnails utility will actually cause the thumbnail to be created.
            # Previously, this method was only called in the __str__ method
            self.get_thumbnail_url()
        else:
            self.has_thumbnail = False

    def __str__(self) -> str:
        _str = f"""DirEntry:  is_dir = {self.is_dir} name = {self.name} name_url = {self.name_url}
                  size = {self.size} last_modify_time = {self.last_modify_time} has_thumbnail = {self.has_thumbnail}
                  thumbnail_url = {self.get_thumbnail_url()}"""
        return _str

    def __repr__(self) -> str:
        return self.__str__()

    def get_thumbnail_url(self) -> Optional[str]:
        if self.has_thumbnail:
            if not self.thumbnail_url:
                image = get_thumbnail(self.image_link_path, THUMBNAIL_GEOMETRY)
                self.thumbnail_url = reverse('thumb', args=[image.name])
            return self.thumbnail_url
        return None

#    return dirPath.encode('utf8')

# def getCurrentDirEntriesSearch(folder, path, show_hidden, searchRegexStr):
#    if logger.isEnabledFor(DEBUG):
#        logger.debug("getCurrentDirEntriesSearch: folder = %s path = %s searchRegexStr = %s", folder, path, searchRegexStr)

#    searchRegex = re.compile(searchRegexStr)
#    returnList = []
#    thisEntry = DirEntry(True, path, 0, datetime.fromtimestamp(getmtime(getPath(folder.local_path, path))), folder, path)
#    __getCurrentDirEntriesSearch(folder, path, show_hidden, searchRegex, thisEntry, returnList)

#    for entry in returnList:
#        entry.name = "/".join([entry.currentPathOrig, entry.name])

#    return returnList

# def __getCurrentDirEntriesSearch(folder, path, show_hidden, searchRegex, thisEntry, returnList):
#    if logger.isEnabledFor(DEBUG):
#        logger.debug("getCurrentDirEntriesSearch:  folder = %s path = %s searchRegex = %s thisEntry = %s", folder, path, searchRegex, thisEntry)
#    entries = get_current_dir_entries(folder, path, show_hidden)

#    includeThisDir = False

#    for entry in entries:
#        try:
#            if searchRegex.search(entry.name):
#                if logger.isEnabledFor(DEBUG):
#                    logger.debug("including this dir")
#                includeThisDir = True
#            elif entry.is_dir:
#                __getCurrentDirEntriesSearch(folder, "/".join([path, entry.name]), show_hidden, searchRegex, entry, returnList)
#        except UnicodeDecodeError as e:
#            logger.error('UnicodeDecodeError: %s', entry.name)

#    if includeThisDir:
#        returnList.append(thisEntry)


def replace_escaped_url(url: str) -> str:
    url = html.unescape(url)
    return url.replace("(comma)", ",").replace("(ampersand)", "&")


def handle_delete(folder_and_path: FolderAndPath, entries: List[str]) -> None:
    for entry in entries:
        entry_path = join_paths(folder_and_path.abs_path, replace_escaped_url(entry)).encode("utf-8")

        if os.path.isdir(entry_path):
            rmtree(entry_path)
        else:
            logger.info("handleDelete: login = %s", os.getlogin())
            os.remove(entry_path)


def format_bytes(num_bytes: int, force_unit: Optional[str] = None, include_unit_suffix=True) -> str:
    if force_unit:
        unit = force_unit
    else:
        unit = get_bytes_unit(num_bytes)

    if unit == "GB":
        return_value = f"{(num_bytes / GIGABYTE):.2f}"
    elif unit == "MB":
        return_value = f"{(num_bytes / MEGABYTE):.2f}"
    elif unit == "KB":
        return_value = f"{(num_bytes / KILOBYTE):.2f}"
    else:
        return_value = str(num_bytes)

    if include_unit_suffix and unit != "Bytes":
        return f"{return_value} {unit}"
    return return_value


def get_bytes_unit(num_bytes: int) -> str:
    if num_bytes / GIGABYTE > 1:
        return "GB"
    if num_bytes / MEGABYTE > 1:
        return "MB"
    if num_bytes / KILOBYTE > 1:
        return "KB"
    return "Bytes"


def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None
