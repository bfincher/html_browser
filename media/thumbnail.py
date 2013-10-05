import Image
import re
import math
import os
import sys
import shutil

imagePattern = re.compile("(.+(\\.(?i)(jpg|png|gif|bmp))$)")
imageExtensionPattern = re.compile("(\\.(?i)(jpg|png|gif|bmp))$")

imageTypes = {'JPG' : 'JPEG',
               'jpg' : 'JPEG',
               'PNG' : 'PNG',
               'png' : 'PNG',
	       'GIF' : 'GIF',
	       'gif' : 'GIF',
	       'BMP' : 'BMP',
	       'bmp' : 'BMP'}

class Thumbnail():
    def __init__(self, basePath, baseThumbsDir):
        self.basePath = basePath
	self.baseThumbsDir = baseThumbsDir

    def acceptFile(self, dir, name):
	if name == "lost+found":
	    return False

        if os.path.isdir(os.path.join(dir, name)):
	    return name != "thumbs"
	else:
	    if imagePattern.match(name):
	        thumbsDir = self.getThumbsDir(dir)
	        if os.path.exists(thumbsDir) and os.path.isdir(thumbsDir):
		    return not os.path.exists(os.path.join(thumbsDir, name))
		else:
		    return True

        return False

    def getThumbsDir(self, dir):
        path = dir.replace(self.basePath, "")
	if len(path) > 0:
	    thumbsDir = os.path.join(self.baseThumbsDir, path)
	else:
	    thumbsDir = self.baseThumbsDir

	if not os.path.exists(thumbsDir):
	    os.makedirs(thumbsDir)

	return thumbsDir

    def processDir(self, dir):
        #print "processing dir %s" % dir
        for f in os.listdir(dir):
	    if not self.acceptFile(dir, f):
	        continue

	    file = os.path.join(dir, f)
            if os.path.isdir(file):
                self.processDir(file)
            else:
                print "Processing %s" % file
                try:
                    im = Image.open(file)
                    im.thumbnail((150, 150), Image.ANTIALIAS)

                    thumbsDir = self.getThumbsDir(dir)
                    destFile = os.path.join(thumbsDir, f)
                    extension = getFileExtension(f)[1:]

                    im.save(destFile,  imageTypes[extension])
                except IOError as e:
                    print e

    def renameLargeFiles(self, dir):
        print "renameLargeFiles processing dir %s" % dir
        count = 1
        for root, dirs, files in os.walk(dir):
            for f in files:
                if not self.acceptFile(root, f):
                    continue

                file = os.path.join(root, f)
                if os.path.isdir(file):
                    self.renameLargeFiles(file)
                elif len(f) > 15:
                    while True:
                        newFileName = "IMG_"
                        zeroes = 4 - int(math.log(count, 10))
                        for i in range(zeroes):
                            newFileName = newFileName + "0"
                        newFileName = newFileName + str(count)
                        count +=1

                        extension = getFileExtension(f)
                        newFileName = newFileName + extension

                        if not os.path.exists(newFileName):
                            break

                    print "Renaming %s to %s" % (f, newFileName)
                    os.rename(file, os.path.join(root, newFileName))
	        


def deleteObsoleteThumbs(picDir, thumbDir):
    for file in os.listdir(thumbDir):
        thumbFile = os.path.join(thumbDir, file)
        picFile = os.path.join(picDir, file)
        if os.path.exists(picFile):
	    if os.path.isdir(picFile):
	        deleteObsoleteThumbs(picFile, thumbFile)
	else:
	    print "Deleting %s" % thumbFile
	    if os.path.isdir(thumbFile):
	        shutil.rmtree(thumbFile)
	    else:
	        os.remove(thumbFile)

def getFileExtension(f):
    name, extension = os.path.splitext(f)
    return extension

def main(argv):
    baseDir = argv[1]
    baseDirName = os.path.basename(os.path.normpath(baseDir))
    basePath = baseDir.replace(baseDirName, "")
    baseThumbsDir = argv[2]
    thumb = Thumbnail(basePath, baseThumbsDir)

    print "basePath = %s, baseThumbsDir = %s" % (basePath, baseThumbsDir)

    print "renaming large file names"
    thumb.renameLargeFiles(baseDir)
    print "processing %s" % baseDir
    thumb.processDir(baseDir)
    print "deleting obsolete thumbs"
    deleteObsoleteThumbs(basePath, baseThumbsDir)


    
if __name__ == "__main__":
    main(sys.argv)
