#
# Regular cron jobs for the openio-sds-rsyslog package
#
0 4	* * *	root	[ -x /usr/bin/openio-sds-rsyslog_maintenance ] && /usr/bin/openio-sds-rsyslog_maintenance
