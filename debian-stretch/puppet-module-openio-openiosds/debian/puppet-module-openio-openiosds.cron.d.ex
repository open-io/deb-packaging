#
# Regular cron jobs for the puppet-module-openio-openiosds package
#
0 4	* * *	root	[ -x /usr/bin/puppet-module-openio-openiosds_maintenance ] && /usr/bin/puppet-module-openio-openiosds_maintenance
