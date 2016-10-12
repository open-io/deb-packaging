#
# Regular cron jobs for the python-django-redis-cache package
#
0 4	* * *	root	[ -x /usr/bin/python-django-redis-cache_maintenance ] && /usr/bin/python-django-redis-cache_maintenance
