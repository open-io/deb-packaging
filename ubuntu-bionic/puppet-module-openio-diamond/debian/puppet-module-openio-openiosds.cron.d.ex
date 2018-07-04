#
# Regular cron jobs for the puppet-module-openio-diamond package
#
0 4	* * *	root	[ -x /usr/bin/puppet-module-openio-diamond_maintenance ] && /usr/bin/puppet-module-openio-diamond_maintenance
