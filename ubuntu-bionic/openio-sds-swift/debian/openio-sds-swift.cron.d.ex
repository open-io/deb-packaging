#
# Regular cron jobs for the openio-sds-swift package
#
0 4	* * *	root	[ -x /usr/bin/openio-sds-swift_maintenance ] && /usr/bin/openio-sds-swift_maintenance
