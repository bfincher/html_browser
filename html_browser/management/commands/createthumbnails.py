from django.core.management.base import BaseCommand, CommandError
from sorl.thumbnail import default # type: ignore
from sorl.thumbnail.images import ImageFile # type: ignore

from html_browser import utils
from html_browser._os import join_paths
from html_browser.constants import _constants as constants
from html_browser.models import Folder
from html_browser.utils import FolderAndPath


class Command(BaseCommand):
    help = 'creates thumbnails for images in the specified folders'

    def add_arguments(self, parser):
        parser.add_argument('folder_names', nargs='+', type=str)

    def handle(self, *args, **options):
        for folder_name in options['folder_names']:
            try:
                folder = Folder.objects.get(name=folder_name)
            except Folder.DoesNotExist:
                raise CommandError(f"The folder {folder_name} does not exist") #pylint: disable=raise-missing-from

            folder_and_path = FolderAndPath(folder=folder, path='')
            self._process_entries(folder_and_path)

    def _process_entries(self, folder_and_path):
        # first iterate through entries in details view (does not create thumbnail)
        # to determine if a thumbnail needs to be created
        log_entries = []
        for entry in folder_and_path.get_dir_entries(True, constants.details_view_type):
            if not entry.is_dir and utils.imageRegex.match(entry.name):
                image_link_path = join_paths(folder_and_path.folder.local_path, folder_and_path.relative_path, entry.name)
                options = {}
                for key, value in default.backend.default_options.items():
                    options.setdefault(key, value)
                source = ImageFile(image_link_path)
                file_name = default.backend._get_thumbnail_filename(source, utils.THUMBNAIL_GEOMETRY, options)  #pylint: disable=protected-access

                thumbnail = ImageFile(file_name, default.storage)
                cached = default.kvstore.get(thumbnail)
                if not cached:
                    log_entries.append(entry.name)

        for entry in folder_and_path.get_dir_entries(True, constants.thumbnails_view_type):
            if entry.is_dir:
                self.stdout.write(f"Processing dir {entry.name}")
                child_folder = FolderAndPath(folder=folder_and_path.folder, path=join_paths(folder_and_path.relative_path, entry.name))
                self._process_entries(child_folder)
            elif entry.name in log_entries:
                self.stdout.write('Creating thumbnail for {folder_and_path.folder.local_path}{folder_and_path.relative_path}/{entry.name}')
