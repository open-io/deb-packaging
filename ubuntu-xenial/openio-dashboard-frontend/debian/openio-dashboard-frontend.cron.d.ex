#
# Regular cron jobs for the openio-dashboard-frontend package
#
0 4	* * *	root	[ -x /usr/bin/openio-dashboard-frontend_maintenance ] && /usr/bin/openio-dashboard-frontend_maintenance
