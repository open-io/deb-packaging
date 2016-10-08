#
# Regular cron jobs for the openio-dashboard-backend package
#
0 4	* * *	root	[ -x /usr/bin/openio-dashboard-backend_maintenance ] && /usr/bin/openio-dashboard-backend_maintenance
