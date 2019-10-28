#
# Regular cron jobs for the openio-sds-swift-extended package
#
0 4	* * *	root	[ -x /usr/bin/openio-sds-swift-extended_maintenance ] && /usr/bin/openio-sds-swift-extended_maintenance
