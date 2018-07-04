#
# Regular cron jobs for the python-engineio package
#
0 4	* * *	root	[ -x /usr/bin/python-engineio_maintenance ] && /usr/bin/python-engineio_maintenance
