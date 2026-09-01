#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

<<<<<<< HEAD
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resq_backend.settings')
=======

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safecampus_project.settings')
>>>>>>> 475fb2e0677ff423b8bd020190bffa279649146c
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

<<<<<<< HEAD
=======

>>>>>>> 475fb2e0677ff423b8bd020190bffa279649146c
if __name__ == '__main__':
    main()
