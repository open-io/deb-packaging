#
# Regular cron jobs for the openio-sds-logrotate package
#
0 4	* * *	root	[ -x /usr/bin/openio-sds-logrotate_maintenance ] && /usr/bin/openio-sds-logrotate_maintenance
