#
# Regular cron jobs for the openio-asn1c package
#
0 4	* * *	root	[ -x /usr/bin/openio-asn1c_maintenance ] && /usr/bin/openio-asn1c_maintenance
