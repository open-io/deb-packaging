#
# Regular cron jobs for the puppet-module-openio-gridinit package
#
0 4	* * *	root	[ -x /usr/bin/puppet-module-openio-gridinit_maintenance ] && /usr/bin/puppet-module-openio-gridinit_maintenance
