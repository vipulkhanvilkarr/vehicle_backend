# Avoid importing the Celery app at Django import time to prevent
# tasks from being discovered/imported before Django's app registry is ready.
# Import the Celery app explicitly from `config.celery_app` in worker entrypoints when needed.

__all__ = ()
