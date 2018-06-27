#
# Regular cron jobs for the openio-gridinit package
#
0 4	* * *	root	[ -x /usr/bin/openio-gridinit_maintenance ] && /usr/bin/openio-gridinit_maintenance
