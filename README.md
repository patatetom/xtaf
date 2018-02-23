# xtaf
Xbox 360 file system

```
Python 3.6.4 (default, Jan  5 2018, 02:35:40) 
[GCC 7.2.1 20171224] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import xb360hd
>>> # Xbox 360 hard drive is accessible from /dev/loop0
>>> dev = '/dev/loop0'
>>> fx = xb360hd.Fatx(dev)
>>> fx
(id: 2068792064, size: 244943675392, cluster size: 16384, fat entry: 4, fat size: 59801600, root cluster: 1)
>>> fx.device
(device name: /dev/loop0, serial number: 6VCT9Z2W, firmware revision: 0002CE02, model number: ST9250315AS,
number of sectors: 488397168, logical size: 250059350016)
>>> fx.root
[(filename: name.txt, attribute: 0, size: 22, cdate: 20051122125142, mdate: 20051122125142, first cluster: 2),
(filename: Cache, attribute: 16, size: 0, cdate: 20051122125142, mdate: 20051122125142, first cluster: 3),
(filename: Content, attribute: 16, size: 0, cdate: 20051122125642, mdate: 20051122125642, first cluster: 4)]
>>> fx.fat[:16]
[4294967288, 4294967295, 4294967295, 4294967295, 4294967295, 4294967295, 4294967295, 4294967295, 9, 10, 11, 19,
4294967295, 4294967295, 4294967295, 16]
```
