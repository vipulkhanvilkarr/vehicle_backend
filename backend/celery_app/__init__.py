# Do not import task modules at package import time.
# Importing tasks here can cause Django to import models before apps are loaded,
# leading to "Apps aren't loaded yet." errors during Django startup.
# Celery workers should discover tasks (e.g., via autodiscover_tasks) or import
# them explicitly when starting the worker instead of importing them here.
