#
# Regular cron jobs for the python-djangorestframework-jwt package
#
0 4	* * *	root	[ -x /usr/bin/python-djangorestframework-jwt_maintenance ] && /usr/bin/python-djangorestframework-jwt_maintenance
