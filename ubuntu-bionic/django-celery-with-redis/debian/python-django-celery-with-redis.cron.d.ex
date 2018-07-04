#
# Regular cron jobs for the python-django-celery-with-redis package
#
0 4	* * *	root	[ -x /usr/bin/python-django-celery-with-redis_maintenance ] && /usr/bin/python-django-celery-with-redis_maintenance
