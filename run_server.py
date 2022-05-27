#!./venv/Scripts/python3

from os import environ
from multiprocessing import Process
from subprocess import Popen
from sys import argv
from function_manage import main
from copy import deepcopy
from server_config import server_port, listen_addr
from server_config import background_sleep_time as delay
from pathing_info import python_env, manage

argl = deepcopy(argv)
environ['PYTHONUNBUFFERED'] = "1"

arg_task = [python_env, manage, 'process_tasks', '--sleep', str(delay)]

if __name__ == '__main__':
    argl.append("runserver")
    argl.append("%s:%s" % (listen_addr, server_port))
    argl.append("--noreload")
    p1 = Process(target=main, args=argl)
    p2 = Popen(arg_task)
    p1.start()
    p1.join()
    p2.communicate()
    p2.wait()
    exit(p1.exitcode)
