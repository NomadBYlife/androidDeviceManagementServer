#!/usr/bin/env python3

import venv
import os
import sys
from platform import system
from subprocess import Popen, PIPE

from pathing_info import basedir, python_env, pip_env

from log_config import set_log_level

log = set_log_level()

if system() != 'Windows':
    def get_interpreter_version(interpreter):
        p = Popen([interpreter, '--version'], stdout=PIPE, stderr=PIPE)
        stdout_dirty, stderr_dirty = p.communicate()
        p.wait()
        stdout = stdout_dirty.decode().strip()
        stderr = stderr_dirty.decode().strip()
        ex_code = p.returncode
        if ex_code > 0:
            log.critical(stdout)
            log.critical(stderr)
            log.critical(ex_code)
            return None
        return stdout

    def check_interpreter(interpreter):
        for path in os.environ["PATH"].split(os.pathsep):
            executable = os.path.join(path, interpreter)
            if os.path.isfile(executable) and os.access(executable, os.X_OK):
                return executable
        return None

    def get_highest_python_version():
        def use_3_check_version(interpreter):
            stdout = get_interpreter_version(interpreter)
            if stdout is None:
                return None
            version_list = ['Python 3.7', 'Python 3.6']
            for version in version_list:
                if version in stdout:
                    return interpreter
            return None

        explicit_interpreter_list = ['python3.7', 'python3.6']

        for interpreter in explicit_interpreter_list:
            possible_interpreter = check_interpreter(interpreter)
            if possible_interpreter is not None:
                return possible_interpreter
        return use_3_check_version('python3')

    prefered_interpreter = get_highest_python_version()
    if prefered_interpreter is None:
        log.critical("Error! Highest available Python version is < 3.6")
        exit(95)

    def use_other_version(other_version):
        p = Popen([other_version, 'setup_server.py'])
        p.communicate()
        p.wait()
        exit(p.returncode)

    prefered_interpreter_version = get_interpreter_version(prefered_interpreter)
    if sys.version_info <= (3, 7) and 'Python 3.7' in prefered_interpreter_version:
        use_other_version(prefered_interpreter)

    if sys.version_info <= (3, 6) and 'Python 3.6' in prefered_interpreter_version:
        use_other_version(prefered_interpreter)

    if sys.version_info <= (3, 6):
        log.critical("Minimum Python version is 3.6, please upgrade.")
        exit(95)

try:
    venv.create(os.path.join(basedir, "venv"), with_pip=True)
except PermissionError as pe:
    print(pe)
    print("Does your user have the necessary permissions?")
    exit(96)

os.environ['PYTHONUNBUFFERED'] = "1"
p = Popen([python_env, '-m', 'pip', 'install', '--upgrade', 'pip'])
p.communicate()
p.wait()
req_txt = os.path.join(basedir, 'requirements.txt')
command = [pip_env, 'install', '--no-cache-dir', '-r', req_txt]
p = Popen(command)
p.communicate()
p.wait()
