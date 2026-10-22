#!/usr/bin/env python3
"""Django command entrypoint for Python Sentinel."""
import os
import sys
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinel_site.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
