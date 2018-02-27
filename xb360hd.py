sectorSize = 0x200


from os import path
from struct import unpack
from binascii import hexlify

path.sep = '/'


class Xbox360HardDrive:
    """
    Offset        Length          Information                     Format
    0x2000        0x204-0x80000   Security Sector                 Binary
    0x80000       0x80000000      System Cache                    SFCX (Secure File Cache for Xbox)
    0x80080000    0xa0e30000      Game Cache                      SFCX (Secure File Cache for Xbox)
    0x10c080000   0xce30000       SysExt                          FATX ("Sub"-Partition)
    0x118eb0000   0x8000000       SysExt2                         FATX ("Sub"-Partition)
    0x120eb0000   0x10000000      Xbox 1 Backwards Compatibility  FATX
    0x130eb0000   end of drive    Data                            FATX
    """
    def __init__(self, device, verbose = False):
        self.verbose = verbose
        self.device = open(device, 'rb')
        self.size = self.device.seek(0, 2)
        
        self.defaultOffset = 0
        self.defaultLength = sectorSize
        
        if self.read(0x2204, 0x8) == b'\x89PNG\r\n\x1a\n' :
            unpacked = unpack('<20s8s40s20xI', self.read(0x2000, 0x5c))
            self.serialNumber, self.firmwareRevision, self.modelNumber, sectorsNumber = unpacked
            
            self.serialNumber = self.serialNumber.decode('ascii').strip()
            self.firmwareRevision = self.firmwareRevision.decode('ascii').strip()
            self.modelNumber = self.modelNumber.decode('ascii').strip()
            self.size = sectorsNumber * sectorSize
    
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
    def __init__(self, rawEntry):
        unpacked = unpack('>BB42sIIHHHH4x', rawEntry)
        self.fileNameLength, self.attribute, fileName, self.firstCluster, self.size, cDate, cTime, mDate, mTime = unpacked
        
        if self.fileNameLength < 0x2b : self.fileName = fileName[:self.fileNameLength].decode('ascii')
        else:
            try : fileName = fileName.rstrip(b'\xff').decode('ascii')
            except UnicodeDecodeError : fileName = hexlify(fileName.rstrip(b'\xff')).decode('ascii')
            self.fileName = '<DELETED:{}>'.format(fileName)
        
        self.creationDate = self.__convert(cDate, cTime)
        self.modificationDate = self.__convert(mDate, mTime)
    
    def __repr__(self):
        string  = 'file name: {}, '.format(self.fileName)
        string += 'attribute: {}, '.format(self.attribute)
        string += 'size: {}, '.format(self.size)
        string += 'creation date: {}, '.format(self.creationDate)
        string += 'modification date: {}, '.format(self.modificationDate)
        string += 'first cluster: {}'.format(self.firstCluster)
        return '({})'.format(string)
    
    def __convert(self, fatDate, fatTime):
        return int(
            '{}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(
                (1980 + (fatDate >> 9)),
                ((fatDate >> 5) & 0x0f),
                (fatDate & 0x1f),
                (fatTime >> 11),
                ((fatTime >> 5) & 0x3f),
                ((fatTime & 0x1f) * 2)
            )
        )


class Fatx:
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
        
        self.device.defaultOffset = offset + 0x1000 + self.tableSize
        
        self.root = self.getDirectoryEntries(0)
        
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
        if self.verbose : print('{} cluster {}'.format(length and 'reading {} bytes at'.format(length) or 'reading', cluster))
        return self.device.read(cluster * self.clusterSize, length)
    
    def getDirectoryEntries(self, cluster):
        # TODO : can be more than one cluster
        if cluster < 0 or cluster > self.tableSize : raise ValueError('unauthorized value ({}) for cluster'.format(cluster))
        data = self.readCluster(cluster).rstrip(b'\xff' * 0x40)
        if len(data) % 0x40 : raise ValueError('wrong directory entries length ({})'.format(len(data)))
        return {entry.fileName: entry for entry in [DirectoryEntry(data[index:index + 0x40]) for index in range(0, len(data), 0x40)]}
    
    def isDirectory(self, entry):
        return entry.attribute & 0x10
    
    def getPathEntries(self, pathName):
        if not pathName.startswith('/') : raise ValueError('path name must start with /')
        pathName = path.abspath(pathName).rstrip('/').lstrip('/')
        if self.verbose : print('get entries for {}'.format(pathName or '/'))
        if not pathName : return self.root
        # TODO : could be recursive
        directoryEntries = self.root
        for directory in pathName.split(path.sep):
            try : entry = directoryEntries[directory]
            except KeyError : raise KeyError('directory {} not found'.format(directory))
            if not self.isDirectory(entry) : raise ValueError('{} is not a directory'.format(directory))
            directoryEntries = self.getDirectoryEntries(entry.firstCluster)
        return directoryEntries
    
    def getFileEntry(self, fileName):
        if not fileName.startswith('/') : raise ValueError('file name must start with /')
        if self.verbose : print('get entry for {}'.format(fileName))
        pathName, fileName = path.split(path.abspath(fileName))
        directoryEntries = self.getPathEntries(pathName)
        if self.verbose : print('get entry for {}'.format(fileName))
        try : fileEntry = directoryEntries[fileName]
        except KeyError : raise KeyError('file {} not found'.format(fileName))
        if self.isDirectory(fileEntry) : raise ValueError('{} is a directory'.format(fileName))
        return fileEntry
    
    def getDirectories(self, directoryEntries):
        return {fileName: entry for fileName, entry in directoryEntries.items() if self.isDirectory(entry)}
    
    def getFiles(self, directoryEntries):
        return {fileName: entry for fileName, entry in directoryEntries.items() if not self.isDirectory(entry)}
