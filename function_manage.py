#!./venv/Scripts/python3.7
import os


# need a function as target for running tests in Process so we can attach debugging
def main(*args):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'androidDeviceManagementServer.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(args)
