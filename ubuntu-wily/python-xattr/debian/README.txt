In Linux 2.6+, extended attributes are supported by the ext2, ext3, ext4, JFS,
ReiserFS and XFS filesystems.
In Darwin 8.0+ (Mac OS X 10.4), extended are supported by the HFS+ filesystem.

Extended attributes extend the basic attributes of files and directories
in the file system.  They are stored as name:data pairs associated with
file system objects (files, directories, symlinks, etc).

Warning: the behavior of python-xattr on Linux systems may be confusing due to
the presence of the "user." string at the beginning of every attribute name.
Such string is not shown by other tools like "pyxattr" and "attr".

>>> from xattr import xattr
>>> f = xattr('/tmp/testfile')
>>> f.list()
[]
>>> f.set('user.my_color','green')
>>> f.list()
[u'user.my_color']
>>> f.get('user.my_color')
'green'
>>> f.remove('user.my_color')
>>> f.list()
[]

Some documentation is available at:

http://bob.pythonmac.org/archives/2005/10/08/xattr-python-extended-filesystem-attributes/

