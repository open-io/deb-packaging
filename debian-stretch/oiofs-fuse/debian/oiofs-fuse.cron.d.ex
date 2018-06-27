#
# Regular cron jobs for the oiofs-fuse package
#
0 4	* * *	root	[ -x /usr/bin/oiofs-fuse_maintenance ] && /usr/bin/oiofs-fuse_maintenance
