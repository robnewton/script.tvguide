#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import xbmcvfs

class FileWrapper(object):
    def __init__(self, filename):
        if hasattr(xbmcvfs, 'File'):
            #xbmcvfs.File() was added in Frodo
            self.vfsfile = xbmcvfs.File(filename)
            self.size = self.vfsfile.size()
        else:
            print "xbmcvfs.File() is missing - perhaps you are running XBMC Eden? - retrying with python file opener"
            try:
                self.vfsfile = open(filename)
            except IOError:
                xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), 'smb://, nfs://, etc. is not support in Eden', 'Mount these on a system level instead. Filename:', filename)
            self.size = os.path.getsize(filename)
        self.bytesRead = 0

    def close(self):
        self.vfsfile.close()

    def read(self, bytes):
        self.bytesRead += bytes
        return self.vfsfile.read(bytes)

    def tell(self):
        return self.bytesRead
