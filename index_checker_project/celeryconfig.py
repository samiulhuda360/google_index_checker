# celeryconfig.py
broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/0'
broker_connection_retry_on_startup = True