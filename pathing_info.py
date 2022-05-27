import os
from platform import system
basedir = os.path.dirname(__file__)


def os_folder_switch(os):
    switch = {
        'Windows': 'Scripts',
        'Linux': 'bin'
    }
    return switch.get(os, '---OS-NOT-SUPPORTED---')


os_folder = os_folder_switch(system())
python_env = os.path.abspath(os.path.join(basedir, "venv/%s/python" % os_folder))
pip_env = os.path.abspath(os.path.join(basedir, "venv/%s/pip" % os_folder))
manage = os.path.abspath(os.path.join(basedir, "manage.py"))
