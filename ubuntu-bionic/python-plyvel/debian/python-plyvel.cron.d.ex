#
# Regular cron jobs for the python-plyvel package
#
0 4	* * *	root	[ -x /usr/bin/python-plyvel_maintenance ] && /usr/bin/python-plyvel_maintenance
