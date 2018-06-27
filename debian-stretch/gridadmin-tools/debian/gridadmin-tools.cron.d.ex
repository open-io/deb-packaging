#
# Regular cron jobs for the gridadmin-tools package
#
0 4	* * *	root	[ -x /usr/bin/gridadmin-tools_maintenance ] && /usr/bin/gridadmin-tools_maintenance
