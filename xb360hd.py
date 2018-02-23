sectorSize = 0x200


from hashlib import sha1
from struct import unpack


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
        self.device.seek(self.defaultOffset + offset)
        return self.device.read(length or self.defaultLength)


class DirEntry:
    def __init__(self, rawEntry):
        unpacked = unpack('>BB42sIIHHHH4x', rawEntry)
        self.filenameLength, self.attribute, self.filename, self.firstCluster, self.size, cDate, cTime, mDate, mTime = unpacked
        self.filename = self.filename.rstrip(b'\xff').decode('ascii')
        if self.filenameLength != len(self.filename) : raise ValueError
        self.cDate = self.__convert(cDate, cTime)
        self.mDate = self.__convert(mDate, mTime)
    
    def __repr__(self):
        string  = 'filename: {}, '.format(self.filename)
        string += 'attribute: {}, '.format(self.attribute)
        string += 'size: {}, '.format(self.size)
        string += 'cdate: {}, '.format(self.cDate)
        string += 'mdate: {}, '.format(self.mDate)
        string += 'first cluster: {}'.format(self.firstCluster)
        return '({})'.format(string)
    
    def __convert(self, fatDate, fatTime):
    # https://www.snip2code.com/Snippet/263353/Python-functions-to-convert-timestamps-i
        return int(
            '{}{}{}{}{}{}'.format(
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
        if magic != b'XTAF' : raise TypeError
        if not sectors : raise ValueError
        
        self.size = size
        if not self.size : self.size = self.device.size - self.device.defaultOffset
        
        self.clusterSize = sectors * sectorSize
        self.device.defaultLength = self.clusterSize
        
        self.fatEntry = ((self.size / self.clusterSize) < 0xfff5) and 0x2 or 0x4
        
        self.fatSize = int(self.size / self.clusterSize * self.fatEntry)
        if self.fatSize % 0x1000 : self.fatSize += 0x1000 - (self.fatSize % 0x1000)
        
        data = self.device.read(length = self.fatSize, offset = 0x1000).rstrip(b'\x00' * self.fatEntry)
        if len(data) % self.fatEntry : raise ValueError
        format = (self.fatEntry == 0x2) and '>H' or '>I'
        self.fat = [unpack(format, data[index:index + self.fatEntry])[0] for index in range(0, len(data), self.fatEntry)]
        
        data = self.device.read(offset = self.fatSize + 0x1000).rstrip(b'\xff' * 0x40)
        if len(data) % 0x40 : raise ValueError
        self.root = [DirEntry(data[index:index + 0x40]) for index in range(0, len(data), 0x40)]
    
    def __repr__(self):
        string  = 'id: {}, '.format(self.id)
        string += 'size: {}, '.format(self.size)
        string += 'cluster size: {}, '.format(self.clusterSize)
        string += 'fat entry: {}, '.format(self.fatEntry)
        string += 'fat size: {}, '.format(self.fatSize)
        string += 'root cluster: {}'.format(self.rootCluster)
        return '({})'.format(string)
