#
# Regular cron jobs for the openio-sds package
#
0 4	* * *	root	[ -x /usr/bin/openio-sds_maintenance ] && /usr/bin/openio-sds_maintenance
