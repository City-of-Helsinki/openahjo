#!/usr/bin/env python
import os
import sys
import traceback

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openahjo.settings")

    from django.core.management import execute_from_command_line

    try:
        execute_from_command_line(sys.argv)
    except Exception as e:
        if sys.stdout.isatty():
            traceback.print_exc()
        else:
            from django.conf import settings
            if settings.DEBUG or not hasattr(settings, 'RAVEN_CONFIG'):
                raise
            from raven.contrib.django.models import get_client
            exc_info = sys.exc_info()
            if getattr(exc_info[0], 'skip_sentry', False):
                raise
            get_client().captureException(exc_info)
