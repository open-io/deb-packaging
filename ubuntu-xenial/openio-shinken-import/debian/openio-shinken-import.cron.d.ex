#
# Regular cron jobs for the openio-shinken-import package
#
0 4	* * *	root	[ -x /usr/bin/openio-shinken-import_maintenance ] && /usr/bin/openio-shinken-import_maintenance
