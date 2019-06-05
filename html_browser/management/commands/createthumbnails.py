from django.core.management.base import BaseCommand, CommandError
from html_browser.models import Folder
from html_browser.utils import FolderAndPath, getCurrentDirEntries
from html_browser.constants import _constants as constants
from html_browser._os import joinPaths
from html_browser import utils


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
        for entry in getCurrentDirEntries(folderAndPath, True, constants.thumbnailsViewType):
            if entry.isDir:
                childFolder = FolderAndPath(folder=folderAndPath.folder, path=joinPaths(folderAndPath.relativePath, entry.name))
                self.processEntries(childFolder)
            elif utils.imageRegex.match(entry.name):
                self.stdout.write('Creating thumbnail for %s%s/%s' % (folderAndPath.folder.localPath, folderAndPath.relativePath, entry.name))
