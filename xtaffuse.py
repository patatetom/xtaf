from xb360hd import Xtaf
from fuse import FUSE, FuseOSError, Operations
from time import localtime, mktime
from os import getgid, getuid


class XtafFuse(Operations):
    def __init__(self, device, offset = 0x130eb0000, size = 0, verbose = False):
        self.xtaf = Xtaf(device, offset, size, verbose)
        self.ctime = mktime(localtime())
        self.uid = getuid()
        self.gid = getgid()
        self.cacheClusters = {}
    
    def getattr(self, path, fh):
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
        stat.update({
            'st_mode': 0o100444,
            'st_nlink': 1,
            'st_size': entry.size
        })
        if entry.fileName.startswith('(DELETED:') : stat.update({'st_mode': 0o100000})
        return stat

    def readdir(self, path, fh):
        pathEntries = (path == '/') and self.xtaf.root or self.xtaf.getDirectoryEntries(self.xtaf.getEntry(path))
        return ('.', '..') + tuple(pathEntries.keys())
    
    def read(self, path, size, offset, fh):
        data = b''
        if not size : return data
        if '/(DELETED:' in path : raise FuseOSError(1)
        entry = self.xtaf.getEntry(path)
        if offset >= entry.size : return data
        clusters = self.cacheClusters.get(entry)
        if not clusters:
            clusters = self.xtaf.getClusters(entry)
            self.cacheClusters[entry] = clusters
        start = offset // self.xtaf.clusterSize
        stop = start + (size // self.xtaf.clusterSize) + (size % self.xtaf.clusterSize > 0)
        clusters = clusters[start:stop]
        for cluster in clusters : data += self.xtaf.readCluster(cluster)
        return data[:size]
