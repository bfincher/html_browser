from django.core.management.base import BaseCommand, CommandError
from html_browser.models import Folder
from html_browser.utils import FolderAndPath, getCurrentDirEntries
from html_browser.constants import _constants as constants
from html_browser._os import joinPaths
from html_browser import utils
from sorl.thumbnail.images import ImageFile
from sorl.thumbnail import default


class Command(BaseCommand):
    help = 'creates thumbnails for images in the specified folders'

    def add_arguments(self, parser):
        parser.add_argument('folder_names', nargs='+', type=str)

    def handle(self, *args, **options):
        for folderName in options['folder_names']:
            try:
                folder = Folder.objects.get(name=folderName)
            except Folder.DoesNotExist:
                raise CommandError("The folder %s does not exist" % folderName)

            folderAndPath = FolderAndPath(folder=folder, path='')
            self.processEntries(folderAndPath)

    def processEntries(self, folderAndPath):
        # first iterate through entries in details view (does not create thumbnail)
        # to determine if a thumbnail needs to be created
        logEntries = []
        for entry in getCurrentDirEntries(folderAndPath, True, constants.detailsViewType):
            if not entry.isDir and utils.imageRegex.match(entry.name):
                imageLinkPath = joinPaths(folderAndPath.folder.localPath, folderAndPath.relativePath, entry.name)
                options = {}
                for key, value in default.backend.default_options.items():
                    options.setdefault(key, value)
                source = ImageFile(imageLinkPath)
                fileName = default.backend._get_thumbnail_filename(source, utils.thumbnailGeometry, options)

                thumbnail = ImageFile(fileName, default.storage)
                cached = default.kvstore.get(thumbnail)
                if not cached:
                    logEntries.append(entry.name)

        for entry in getCurrentDirEntries(folderAndPath, True, constants.thumbnailsViewType):
            if entry.isDir:
                self.stdout.write("Processing dir %s" % entry.name)
                childFolder = FolderAndPath(folder=folderAndPath.folder, path=joinPaths(folderAndPath.relativePath, entry.name))
                self.processEntries(childFolder)
            elif entry.name in logEntries:
                self.stdout.write('Creating thumbnail for %s%s/%s' % (folderAndPath.folder.localPath, folderAndPath.relativePath, entry.name))
