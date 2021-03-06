# xtaf
Xbox 360 file system


## xtaffuse module
this module use `xb360hd` module to read a xtaf partition

```
Python 3.6.4 (default, Jan  5 2018, 02:35:40) 
[GCC 7.2.1 20171224] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> # import module
>>> import xtaffuse

>>> # Xbox 360 hard drive is accessible from /dev/loop0
>>> dev = '/dev/loop0'

>>> # open data partition by default
>>> xtaf = xtaffuse.XtafFuse(dev)
>>> xtaf.xtaf
(id: 2068792064, size: 244943675392, cluster size: 16384, table entry: 4, table size: 59801600,
root cluster: 1, volume name: Disque dur)
>>> xtaf.xtaf.device
(name: /dev/loop0, serial number: 6VCT9Z2W, firmware revision: 0002CE02, model number: ST9250315AS,
size: 250059350016)

>>> # test readdir and getattr functions
>>> xtaf.readdir('/', 0)
('.', '..', 'name.txt', 'Cache', 'Content')
>>> xtaf.readdir('/Content', 0)
('.', '..', 'E00005538DC276AE', '0000000000000000')
>>> xtaf.getattr('/', 0)
{'st_mode': 16749, 'st_nlink': 2, 'st_gid': 1000, 'st_uid': 1000, 'st_size': 4096, 'st_ctime':
1520327391.0, 'st_mtime': 1520327391.0, 'st_atime': 1520327391.0}
>>> xtaf.getattr('/name.txt', 0)
{'st_mode': 33060, 'st_nlink': 1, 'st_gid': 1000, 'st_uid': 1000, 'st_size': 22, 'st_ctime':
1132660302.0, 'st_mtime': 1132660302.0, 'st_atime': 1132660302.0}

>>> # make the partition accessible through /tmp/xbox
>>> fuser = xtaffuse.FUSE(xtaf, '/tmp/xbox', foreground=True, nothreads=True, debug=True)
FUSE library version: 2.9.7
nullpath_ok: 0
nopath: 0
utime_omit_ok: 0
unique: 1, opcode: INIT (26), nodeid: 0, insize: 56, pid: 0
INIT: 7.26
flags=0x001ffffb
max_readahead=0x00020000
   INIT: 7.19
   flags=0x00000011
   max_readahead=0x00020000
   max_write=0x00020000
   max_background=0
   congestion_threshold=0
   unique: 1, success, outsize: 40
```
and in another terminal
```
$ ./isXb360Hd /dev/loop0 -v && echo OK || echo KO
device: /dev/loop0
serial number: 6VCT9Z2W
firmware revision: 0002CE02
model number: ST9250315AS
size: 488397168 bytes
xtaf at 0x10c080000: ok
xtaf at 0x118eb0000: ok
xtaf at 0x120eb0000: ok
xtaf at 0x130eb0000: ok
OK

$ mount | grep /tmp/xbox
XtafFuse on /tmp/xbox type fuse (rw,nosuid,nodev,relatime,user_id=1000,group_id=1000)

$ ll -gG /tmp/xbox/
total 0
dr-xr-xr-x 2 4096 22 nov.   2005 Cache
dr-xr-xr-x 2 4096 22 nov.   2005 Content
-r--r--r-- 1   22 22 nov.   2005 name.txt

$ tree /tmp/xbox/
/tmp/xbox/
├── Cache
│   ├── NB_E0005AE6S4TLE.0000002000000
│   ├── TK_080J90B_A35H6O7QL7FVA.03KR2R4PMB8C2
│   ├── TK_1CKHGOD_7UDM61KKOO9UV.03KR2R4PVDFFI
│   ├── TK_2NHCVSM_BU78383MFBO42.03KR2R4PR916I
│   ├── VC_17SA802_BQFIBU8CS8UT5.03KR2R5IH7L72
│   └── XT_000007V_FK000001H7RBB.03KR2R5C4LKI2
├── Content
│   ├── 0000000000000000
│   │   └── FFFE07DF
│   │       └── 00040000
│   │           ├── (DELETED:XlfsUploadCache.dat)
│   │           └── ContentCache.pkg
│   └── E00005538DC276AE
│       ├── 454109C3
│       │   └── 00000001
│       │       ├── Career 20051122140822
│       │       ├── Career 20051122143225
│       │       ├── Career 20051122143331
│       │       └── Settings 20051122143332
│       └── FFFE07D1
│           └── 00010000
│               └── E00005538DC276AE
└── name.txt
10 directories, 14 files

$ iconv -f utf-16 /tmp/xbox/name.txt
Disque dur

$ xxd /tmp/xbox/Content/E00005538DC276AE/454109C3/00000001/Settings\ 20051122143332 | head
00000000: 434f 4e20 01a8 576c 276a e558 3835 3334  CON ..Wl'j.X8534
00000010: 3239 2d30 3031 0000 0000 0000 0000 0002  29-001..........
00000020: 3037 2d31 392d 3131 0001 0001 31a0 b991  07-19-11....1...
00000030: 4e02 1ca9 0eb1 782c 1c81 60ea b0b5 d29d  N.....x,..`.....
00000040: 420d fb43 89a7 ad2c 871d 2aad 9916 8498  B..C...,..*.....
00000050: f89d 7c2d b6a0 892c ee57 909e f0f5 3259  ..|-...,.W....2Y
00000060: 939e 9e47 9d28 27f3 cb64 67a1 51fa d309  ...G.('..dg.Q...
00000070: ac86 1253 9aad 0aa6 9558 61ef 4aba bdd1  ...S.....Xa.J...
00000080: e167 cfc3 0a72 dc89 2db6 b93d b0be df85  .g...r..-..=....
00000090: 3699 5ca3 9711 56b1 5f62 d6bf c415 5961  6.\...V._b....Ya
```


## xb360hd module
this module is used by `xtaffuse` module to read a xtaf partition : you can use it to debug the module or try to restore a deleted file.

```
Python 3.6.4 (default, Jan  5 2018, 02:35:40) 
[GCC 7.2.1 20171224] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> # import module
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

>>> # play with online directory
>>> xtaf.getEntry('online')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/tmp/xtaf/xb360hd.py", line 194, in getEntry
    if not pathName.startswith('/') : raise ValueError('path name must start with /')
ValueError: path name must start with /
>>> xtaf.getEntry('/online')
get entry for "/online"
(file name: online, attribute: 16, size: 0, creation date: 20120105170952, modification date: 20120105170952,
first cluster: 2)
>>> xtaf.getEntry('/online').isDirectory()
get entry for "/online"
True
>>> xtaf.getDirectoryEntries(xtaf.getEntry('/online'))
get entry for "/online"
get directory entries for online
reading cluster 2
reading 16384 bytes at offset 0x118eba000
{'system.online.manifest.0D1C80138EC7534F': (file name: system.online.manifest.0D1C80138EC7534F,
attribute: 0, size: 6580, creation date: 20171121145842, modification date: 20171121145842,
first cluster: 3), '20446700': (file name: 20446700, attribute: 16, size: 0,
creation date: 20171121145940, modification date: 20171121145940, first cluster: 4),
'(DELETED:system.online.manifest.0CC449508B377299)': (file name:
(DELETED:system.online.manifest.0CC449508B377299), attribute: 0, size: 0, creation date: 20161222095904,
modification date: 20161222095904, first cluster: 1175), '(DELETED:system.online.manifest.082EED04ABC0B778)':
(file name: (DELETED:system.online.manifest.082EED04ABC0B778), attribute: 0, size: 0, creation date:
20140827114954, modification date: 20140827114954, first cluster: 1151),
'(DELETED:system.online.manifest.05675B3DBE8B7702)': (file name:
(DELETED:system.online.manifest.05675B3DBE8B7702), attribute: 0, size: 0, creation date: 20121127181532,
modification date: 20121127181532, first cluster: 1454)}

>>> # play with system.online.manifest.0D1C80138EC7534F file
>>> xtaf.getEntry('/online/system.online.manifest.0D1C80138EC7534F').isDirectory()
get entry for "/online/system.online.manifest.0D1C80138EC7534F"
False
>>> for data in xtaf.readFile(xtaf.getEntry('/online/system.online.manifest.0D1C80138EC7534F')):
...  print(data)
... 
get entry for "/online/system.online.manifest.0D1C80138EC7534F"
reading cluster 3
reading 16384 bytes at offset 0x118ebe000
b'XMNPV\xdf\'7.\x1a~5\xdd\xfa\x93\xb4\x8b\x94\x02\xd1\x85*\x13
…
NewLiveSignup.xex\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
```
