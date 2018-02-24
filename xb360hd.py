sectorSize = 0x200


from hashlib import sha1
from struct import unpack
from binascii import hexlify


class Xbox360HardDrive:
    def __init__(self, device):
        self.device = open(device, 'rb')
        self.defaultOffset = 0
        self.defaultLength = sectorSize
        
        unpacked = unpack('<20s8s40s20xI', self.read(length = 0x5c, offset = 0x2000))
        self.serialNumber, self.firmwareRevision, self.modelNumber, self.sectorsNumber = unpacked
        
        self.serialNumber = self.serialNumber.decode('ascii').strip()
        self.firmwareRevision = self.firmwareRevision.decode('ascii').strip()
        self.modelNumber = self.modelNumber.decode('ascii').strip()
        self.size = self.sectorsNumber * sectorSize
    
    def __repr__(self):
        string  = 'device name: {}, '.format(self.device.name)
        string += 'serial number: {}, '.format(self.serialNumber)
        string += 'firmware revision: {}, '.format(self.firmwareRevision)
        string += 'model number: {}, '.format(self.modelNumber)
        string += 'number of sectors: {}, '.format(self.sectorsNumber)
        string += 'logical size: {}'.format(self.size)
        return '({})'.format(string)
    
    def __del__(self):
        self.device.close()
    
    def read(self, length = 0, offset = 0):
        length = length or self.defaultLength
        offset = self.defaultOffset + offset
        print('reading {} bytes at {}'.format(length, hex(offset)))
        self.device.seek(offset)
        return self.device.read(length)


class DirEntry:
    def __init__(self, rawEntry):
        unpacked = unpack('>BB42sIIHHHH4x', rawEntry)
        self.filenameLength, self.attribute, filename, self.firstCluster, self.size, cDate, cTime, mDate, mTime = unpacked
        self.filename = filename[:self.filenameLength].decode('ascii')
        self.creationDate = self.__convert(cDate, cTime)
        self.modificationDate = self.__convert(mDate, mTime)
    
    def __repr__(self):
        string  = 'filename: {}, '.format(self.filename)
        string += 'attribute: {}, '.format(self.attribute)
        string += 'size: {}, '.format(self.size)
        string += 'creation date: {}, '.format(self.creationDate)
        string += 'modification date: {}, '.format(self.modificationDate)
        string += 'first cluster: {}'.format(self.firstCluster)
        return '({})'.format(string)
    
    def __convert(self, fatDate, fatTime):
    # https://www.snip2code.com/Snippet/263353/Python-functions-to-convert-timestamps-i
        return int(
            '{}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(
                (1980 + ((fatDate >> 9) & 0x7f)),
                ((fatDate >> 5) & 0x0f),
                (fatDate & 0x1f),
                ((fatTime >> 11) & 0x1f),
                ((fatTime >> 5) & 0x3f),
                ((fatTime & 0x1f) * 2)
            )
        )


class Fatx:
    def __init__(self, device, offset = 0x130eb0000, size = 0):
        self.device = Xbox360HardDrive(device)
        self.device.defaultOffset = offset
        
        unpacked = unpack('>4sIII', self.device.read(length = 0x10))
        magic, self.id, sectors, self.rootCluster = unpacked
        if magic != b'XTAF' : raise ValueError('bad magic (0x{})'.format(hexlify(magic).decode('ascii')))
        if not sectors : raise ValueError('no sector allocated')
        
        self.size = size
        if not size : self.size = self.device.size - offset
        
        self.clusterSize = sectors * sectorSize
        self.device.defaultLength = self.clusterSize
        
        self.fatEntry = ((self.size / self.clusterSize) < 0xfff0) and 0x2 or 0x4
        
        self.fatSize = int(self.size / self.clusterSize * self.fatEntry) + 0x1000
        if self.fatSize % 0x1000 : self.fatSize -= self.fatSize % 0x1000
        
        data = self.device.read(length = self.fatSize, offset = 0x1000).rstrip(b'\x00' * self.fatEntry)
        if len(data) % self.fatEntry : raise ValueError('wrong file allocation table length ({})'.format(len(data)))
        format = (self.fatEntry == 0x2) and '>H' or '>I'
        self.fat = [unpack(format, data[index:index + self.fatEntry])[0] for index in range(0, len(data), self.fatEntry)]
        self.device.defaultOffset = offset + 0x1000 + self.fatSize
        
        data = self.device.read().rstrip(b'\xff' * 0x40)
        if len(data) % 0x40 : raise ValueError('wrong root directory length ({})'.format(len(data)))
        self.root = {entry.filename: entry for entry in [DirEntry(data[index:index + 0x40]) for index in range(0, len(data), 0x40)]}
    
    def __repr__(self):
        string  = 'id: {}, '.format(self.id)
        string += 'size: {}, '.format(self.size)
        string += 'cluster size: {}, '.format(self.clusterSize)
        string += 'fat entry: {}, '.format(self.fatEntry)
        string += 'fat size: {}, '.format(self.fatSize)
        string += 'root cluster: {}'.format(self.rootCluster)
        return '({})'.format(string)
