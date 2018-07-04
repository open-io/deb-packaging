#
# Regular cron jobs for the python-socketio2 package
#
0 4	* * *	root	[ -x /usr/bin/python-socketio2_maintenance ] && /usr/bin/python-socketio2_maintenance
