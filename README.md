# xtaf
Xbox 360 file system

```
Python 3.6.4 (default, Jan  5 2018, 02:35:40) 
[GCC 7.2.1 20171224] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import xb360hd

>>> # Xbox 360 hard drive is accessible from /dev/loop0
>>> dev = '/dev/loop0'

>>> # open data partition by default
>>> xtaf = xb360hd.Xtaf(dev)
>>> xtaf
(id: 2068792064, size: 244943675392, cluster size: 16384, fat entry: 4, fat size: 59801600,
root cluster: 1, volume name: Disque dur)
>>> xtaf.device
(device name: /dev/loop0, serial number: 6VCT9Z2W, firmware revision: 0002CE02, model number: ST9250315AS,
number of sectors: 488397168, logical size: 250059350016)
>>> xtaf.root
{'name.txt': (filename: name.txt, attribute: 0, size: 22, creation date: 20051122125142,
modification date: 20051122125142, first cluster: 2), 'Cache': (filename: Cache, attribute: 16, size: 0,
creation date: 20051122125142, modification date: 20051122125142, first cluster: 3),
'Content': (filename: Content, attribute: 16, size: 0, creation date: 20051122125642,
modification date: 20051122125642, first cluster: 4)}
>>> xtaf.fat[:16]
[4294967288, 4294967295, 4294967295, 4294967295, 4294967295, 4294967295, 4294967295, 4294967295, 9, 10, 11,
19, 4294967295, 4294967295, 4294967295, 16]

>>> # bad offset
>>> xtaf = xb360hd.Xtaf(dev, 0x118EB0001, 0x8000000)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/tmp/xb360hd.py", line 83, in __init__
    if magic != b'XTAF' : raise ValueError('bad magic (0x{})'.format(hexlify(magic).decode('ascii')))
ValueError: bad magic (0x54414645)

>>> # open second sysext partition in verbose mode
>>> xtaf = xb360hd.Xtaf(dev, 0x118EB0000, 0x8000000, verbose = True)
reading 92 bytes at offset 0x2000
reading 16 bytes at offset 0x118eb0000
reading 20480 bytes at offset 0x118eb1000
reading cluster 1
reading 16384 bytes at offset 0x118eb6000
>>> xtaf.root
{'online': (filename: online, attribute: 16, size: 0, creation date: 20120105170952,
modification date: 20120105170952, first cluster: 2)}
```
