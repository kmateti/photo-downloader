from shutil import copy2
import os
import glob
import sys
from datetime import datetime


class MediaFile:
    src = ''
    dst = ''
    filename = ''
    ext = ''
    mod_date = 0
    VALID_MEDIA_EXT = ['.jpg', '.cr2', '.mov', '.mts',
                       '.mp4', '.3gp', '.xmp', '.jpeg', '.mpeg', '.mpg', '.png']

    ismedia = False

    def __init__(self, fullfilepath, dstroot):

        # Determine if this file is a media file that we want to save
        self.src = fullfilepath
        pathname, filenamewext = os.path.split(self.src)
        filenamenoext, extension = os.path.splitext(filenamewext)

        for ext in self.VALID_MEDIA_EXT:
            if (extension.lower() == ext):
                self.ismedia = True
                self.filename = filenamenoext
                self.ext = extension  # best to keep case for later path comparison
                self.create_destination_path_string(dstroot)

    def create_destination_path_string(self, dstroot):
        try:
            mtime = os.path.getmtime(self.src)
        except OSError:
            mtime = 0
        
        if (mtime):
            last_mod_date = datetime.fromtimestamp(mtime)

            y = str(last_mod_date.year)
            m = '{:02.0f}'.format(last_mod_date.month)
            d = '{:02.0f}'.format(last_mod_date.day)
            sep = os.path.sep

            self.dst = os.path.normpath(f'{dstroot}{sep}' + \
            f'{y}{sep}{y}-{m}{sep}{y}-{m}-{d}{sep}' + \
            f'{y}{m}{d}_{self.filename}{self.ext}')


    def copy_to_destination_path(self):
        pathname, filename = os.path.split(self.dst)
        
        if (os.path.exists(pathname) == False):
            os.makedirs(pathname)

        copy2(self.src, self.dst)



if __name__ == '__main__':

    srcroot = sys.argv[1]
    dstroot = sys.argv[2]

    print(f'Copying pictures and videos \n from {srcroot} \n to {dstroot} \n')

    allfiles = glob.glob(srcroot + '/**/*.*', recursive=True)

    skippednum = 0
    copyingnum = 0
    nonmedianum = 0

    mlist = list()
    for src in allfiles:
        m = MediaFile(src, dstroot)
        if (m.ismedia):
            fullpath = os.path.normpath(m.dst)
            if os.path.exists(fullpath):
                print(f'Found {m.src} \n in {fullpath}, skipping\n') 
                skippednum += 1
            else:
                print(f'Copying {m.src} \n to {fullpath}\n')
                copyingnum += 1
                mlist.append(m)

        else:
            nonmedianum += 1

    print('\nPhoto download preview: \n')  
    print('------------------------------------------------\n')      
    print(f'Found {str(len(allfiles))} files\n')
    print(f'  {str(nonmedianum)} non-media files\n')
    print(f'  {str(skippednum)} media files will be skipped\n')
    print(f'  {str(copyingnum)} media files copied\n')
    text = input('\nConfirm copy action?[Y/n]:')

    if (text.lower() != 'n'):
        for m in mlist:
            print(f'Copying file to {m.dst}\n')
            m.copy_to_destination_path()
    else:
        print('\nCopying canceled, no action was taken.\n')

