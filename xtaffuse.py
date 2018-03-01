#!/usr/bin/env python3

from xb360hd import Xtaf
from fuse import FUSE, FuseOSError, Operations
from time import localtime, mktime
from os import getgid, getuid

class XtafFuse(Operations):
    def __init__(self, device, offset = 0x130eb0000, size = 0, verbose = False):
        self.xtaf = Xtaf(device, offset = 0x130eb0000, size = 0, verbose = False)
        self.ctime = mktime(localtime())
        self.uid = getuid()
        self.gid = getgid()
    
    def access(self, path, mode):
        pass

    def getattr(self, path, fh=None):
        stat = {
            'st_mode': 0o40555,
            'st_nlink': 2,
            'st_gid': self.gid,
            'st_uid': self.uid,
            'st_size': 0x1000,
            'st_ctime': self.ctime,
            'st_mtime': self.ctime,
            'st_atime': self.ctime
        }
        if path == '/' : return stat
        entry = self.xtaf.getEntry(path)
        ctime = mktime(entry.creationDate.timetuple())
        mtime = mktime(entry.modificationDate.timetuple())
        stat.update({
            'st_ctime': ctime,
            'st_mtime': mtime,
            'st_atime': max(ctime, mtime)
        })
        if entry.isDirectory() : return stat
        # make the <DELETED:> file inaccessible in addition to its null size...
        stat.update({
            'st_mode': 0o100444,
            'st_nlink': 1,
            'st_size': entry.size
        })
        return stat

    def readdir(self, path, fh):
        pathEntries = (path == '/') and self.xtaf.root or self.xtaf.getDirectoryEntries(self.xtaf.getEntry(path))
        for entry in ['.', '..'] + list(pathEntries.keys()) : yield entry
