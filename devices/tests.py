# noinspection PyUnresolvedReferences
from .tests_dir.StaticValTests import StaticValTests
# noinspection PyUnresolvedReferences
from .tests_dir.StatefulTests import StatefulTests, ConcurrentStatefulTests
# noinspection PyUnresolvedReferences
from .tests_dir.AdminTest import *

from os import path as os_path
from pathing_info import basedir

if os_path.exists(os_path.join(basedir, 'systemd_client')):
    # if the systemd client has been checked out from its repository to the local system
    # symlink the 'client' directory there to a directory in this project with the name 'systemd_client'
    # windows: mklink /D <path to client project>\client <path to this project>\systemd_client
    # linux: ln -s <path to client project>\client <path to this project>\systemd_client
    # this will allow the following tests to be run
    # repo location https://gitlab.kobil.com/colin.mcmicken/androiddeviceclientsystemd
    # noinspection PyUnresolvedReferences
    from .tests_dir.SystemDClientTests import SystemDClientTests
