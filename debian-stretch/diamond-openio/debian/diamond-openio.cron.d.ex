#
# Regular cron jobs for the diamond-openio package
#
0 4	* * *	root	[ -x /usr/bin/diamond-openio_maintenance ] && /usr/bin/diamond-openio_maintenance
