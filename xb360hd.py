from os import path
from struct import unpack
from binascii import hexlify
from datetime import datetime

sectorSize = 0x200


class Xbox360HardDrive:
    """
    Security Sector at offset 0x2000
    Offset   Size           Type                Information
    0x0      0x14           ascii string        serial number
    0x14     0x8            ascii string        firmware revision
    0x1c     0x28           ascii string        model number
    0x44     0x14           bytes               MS logo hash
    0x58     0x4            unsigned int (LE)   number of sectors on drive
    0x5c     0x100          bytes               RSA signature
    0x00     0x4            signed int          MS logo Size
    0x04     MS logo size   image PNG           MS logo
    """
    def __init__(self, device, verbose = False):
        self.verbose = verbose
        self.device = open(device, 'rb')
        
        self.defaultOffset = 0
        self.defaultLength = sectorSize
        
        if self.read(0x2204, 0x8) == b'\x89PNG\r\n\x1a\n' :
            unpacked = unpack('<20s8s40s20xI', self.read(0x2000, 0x5c))
            self.serialNumber, self.firmwareRevision, self.modelNumber, sectorsNumber = unpacked
            
            self.serialNumber = self.serialNumber.decode('ascii').strip()
            self.firmwareRevision = self.firmwareRevision.decode('ascii').strip()
            self.modelNumber = self.modelNumber.decode('ascii').strip()
            self.size = sectorsNumber * sectorSize
        else : self.size = self.device.seek(0, 2)
    
    def __repr__(self):
        string  = 'name: {}, '.format(self.device.name)
        if hasattr(self, 'serialNumber') : string += 'serial number: {}, '.format(self.serialNumber)
        if hasattr(self, 'firmwareRevision') : string += 'firmware revision: {}, '.format(self.firmwareRevision)
        if hasattr(self, 'modelNumber') : string += 'model number: {}, '.format(self.modelNumber)
        string += 'size: {}'.format(self.size)
        return '({})'.format(string)
    
    def __del__(self):
        self.device.close()
    
    def read(self, offset = 0, length = 0):
        offset = self.defaultOffset + offset
        length = length or self.defaultLength
        if self.verbose : print('reading {} bytes at offset {}'.format(length, hex(offset)))
        self.device.seek(offset)
        return self.device.read(length)


class DirectoryEntry:
    """
    Offset   Size   Type             Description
    0x0      0x1    byte             file name length (0xe5 for deleted file)
    0x1      0x1    byte             file attributes
    0x2      0x2a   ascii string     padded file name (0x00/0xff)
    0x2c     0x4    unsigned int     first cluster of file (0x0 for empty file)
    0x30     0x4    unsigned int     file size
    0x34     0x2    unsigned short   creation date
    0x36     0x2    unsigned short   creation time
    0x38     0x2    unsigned short   write date
    0x3a     0x2    unsigned short   write time
    0x3c     0x2    unsigned short   access date
    0x3e     0x2    unsigned short   access time
    """
    def __init__(self, rawEntry):
        unpacked = unpack('>BB42sIIHHHH4x', rawEntry)
        self.fileNameLength, self.attribute, fileName, self.firstCluster, self.size, cDate, cTime, mDate, mTime = unpacked
        
        if self.fileNameLength < 0x2b : self.fileName = fileName[:self.fileNameLength].decode('ascii')
        else:
            try : fileName = fileName.rstrip(b'\xff').decode('ascii')
            except UnicodeDecodeError : fileName = hexlify(fileName.rstrip(b'\xff')).decode('ascii')
            self.fileName = '<DELETED:{}>'.format(fileName)
            self.size = 0
        
        self.creationDate = self.__convert(cDate, cTime)
        self.modificationDate = self.__convert(mDate, mTime)
    
    def __repr__(self):
        string  = 'file name: {}, '.format(self.fileName)
        string += 'attribute: {}, '.format(self.attribute)
        string += 'size: {}, '.format(self.size)
        string += 'creation date: {}, '.format(self.creationDate.strftime('%Y%m%d%H%M%S'))
        string += 'modification date: {}, '.format(self.modificationDate.strftime('%Y%m%d%H%M%S'))
        string += 'first cluster: {}'.format(self.firstCluster)
        return '({})'.format(string)
    
    def isDirectory(self):
        return self.attribute & 0x10 and True or False
    
    def isFile(self):
        return not self.isDirectory()
    
    def __convert(self, fatDate, fatTime):
        return datetime(
            (1980 + (fatDate >> 9)),
            ((fatDate >> 5) & 0x0f),
            (fatDate & 0x1f),
            (fatTime >> 11),
            ((fatTime >> 5) & 0x3f),
            ((fatTime & 0x1f) * 2)
        )


class Xtaf:
    """
    Offset        Size            Information            Format
    0x2000        0x204-0x80000   security sector        binary
    0x80000       0x80000000      system cache           SFCX (Secure File Cache for Xbox)
    0x80080000    0xa0e30000      game cache             SFCX (Secure File Cache for Xbox)
    0x10c080000   0xce30000       system extend 1        XTAF
    0x118eb0000   0x8000000       system extend 2        XTAF
    0x120eb0000   0x10000000      Xbox 1 compatibility   XTAF
    0x130eb0000   end of drive    data                   XTAF
    """
    def __init__(self, device, offset = 0x130eb0000, size = 0, verbose = False):
        self.verbose = verbose
        self.device = Xbox360HardDrive(device, verbose)
        self.device.defaultOffset = offset
        
        unpacked = unpack('>4sIII', self.device.read(0, 0x10))
        magic, self.id, sectors, self.rootCluster = unpacked
        
        if magic != b'XTAF' : raise ValueError('bad magic (0x{})'.format(hexlify(magic).decode('ascii')))
        if not sectors : raise ValueError('no sector allocated')
        
        self.size = size
        if not size : self.size = self.device.size - offset
        
        self.clusterSize = sectors * sectorSize
        self.device.defaultLength = self.clusterSize
        
        self.tableEntry = ((self.size / self.clusterSize) < 0xfff0) and 0x2 or 0x4
        
        self.tableSize = int(self.size / self.clusterSize * self.tableEntry) + 0x1000
        if self.tableSize % 0x1000 : self.tableSize -= self.tableSize % 0x1000
        
        data = self.device.read(0x1000, self.tableSize).rstrip(b'\x00' * self.tableEntry)
        if len(data) % self.tableEntry : raise ValueError('wrong file allocation table length ({})'.format(len(data)))
        format = (self.tableEntry == 0x2) and '>H' or '>I'
        self.table = [unpack(format, data[index:index + self.tableEntry])[0] for index in range(0, len(data), self.tableEntry)]
        
        self.device.defaultOffset = offset + 0x1000 + self.tableSize - self.clusterSize
        
        self.root = self.getDirectoryEntries(None)
        
        entry = self.root.get('name.txt')
        if entry and entry.size < 25 : self.volumeName = self.readCluster(entry.firstCluster, entry.size).decode('utf-16')
    
    def __repr__(self):
        string  = 'id: {}, '.format(self.id)
        string += 'size: {}, '.format(self.size)
        string += 'cluster size: {}, '.format(self.clusterSize)
        string += 'table entry: {}, '.format(self.tableEntry)
        string += 'table size: {}, '.format(self.tableSize)
        string += 'root cluster: {}'.format(self.rootCluster)
        if hasattr(self, 'volumeName') : string += ', volume name: {}'.format(self.volumeName)
        return '({})'.format(string)
    
    def readCluster(self, cluster, length = 0):
        if cluster < 1 or cluster > self.tableSize : raise ValueError('unauthorized cluster value ({})'.format(cluster))
        if self.verbose : print('{} cluster {}'.format(length and 'reading {} bytes at'.format(length) or 'reading', cluster))
        return self.device.read(cluster * self.clusterSize, length)
    
    def getDirectoryEntries(self, directoryEntry):
        if not directoryEntry : return self.__getDirectoryEntries(1)
        if self.verbose : print('get directory entries for {}'.format(directoryEntry.fileName))
        if not directoryEntry.isDirectory() : raise ValueError('{} is not a directory'.format(directoryEntry.fileName))
        return self.__getDirectoryEntries(directoryEntry.firstCluster)
    
    def __getDirectoryEntries(self, cluster):
        if cluster > self.tableSize : return {}
        data = self.readCluster(cluster).rstrip(b'\xff' * 0x40)
        if len(data) % 0x40 : raise ValueError('wrong directory entries length ({})'.format(len(data)))
        directoryEntries = {entry.fileName: entry for entry in [DirectoryEntry(data[index:index + 0x40]) for index in range(0, len(data), 0x40)]}
        directoryEntries.update(self.__getDirectoryEntries(self.table[cluster]))
        return directoryEntries
    
    def getEntry(self, pathName):
        if not pathName.startswith('/') : raise ValueError('path name must start with /')
        pathName = path.abspath(pathName).rstrip('/').lstrip('/')
        if self.verbose : print('get entry for "/{}"'.format(pathName))
        if not pathName : return None
        pathName = pathName.split(path.sep)
        pathNames, fileName = pathName[:-1], pathName[-1:].pop()
        entry = self.__getEntry(self.root, pathNames, fileName)
        return entry
    
    def __getEntry(self, directoryEntries, pathNames, fileName):
        if not pathNames:
            try : entry = directoryEntries[fileName]
            except KeyError : raise KeyError('entry "{}" not found'.format(fileName))
            return entry
        directory = pathNames[0]
        try : directoryEntry = directoryEntries[directory]
        except KeyError : raise KeyError('directory "{}" not found'.format(directory))
        directoryEntries = self.getDirectoryEntries(directoryEntry)
        pathNames = pathNames[1:]
        return self.__getEntry(directoryEntries, pathNames, fileName)
    
    def readFile(self, fileEntry):
        if fileEntry.isDirectory() : raise ValueError('{} is a directory'.format(fileEntry.fileName))
        if fileEntry.size == 0 : yield b''
        elif not fileEntry.size > self.clusterSize : yield self.readCluster(fileEntry.firstCluster, fileEntry.size)
        else:
            clusters, cluster = (), fileEntry.firstCluster
            while not cluster > self.tableSize:
                clusters += (cluster,)
                cluster = self.table[cluster]
            lastCluster, clusters = clusters[-1], clusters[:-1]
            for cluster in clusters : yield self.readCluster(cluster)
            yield self.readCluster(lastCluster)[:fileEntry.size % self.clusterSize]
