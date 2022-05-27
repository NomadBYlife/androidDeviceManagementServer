#!./venv/Scripts/python3

from os import environ
from multiprocessing import Process
from sys import argv
from function_manage import main
from copy import deepcopy

argl = deepcopy(argv)
environ['PYTHONUNBUFFERED'] = "1"

if __name__ == '__main__':
    argl.append("test")
    # argl.append("--debug-mode")
    # argl.append("devices.tests.SystemDClientTests.test_client_function_get_neg_fun_dne")
    p = Process(target=main, args=argl)
    p.start()
    p.join()
    exit(p.exitcode)
