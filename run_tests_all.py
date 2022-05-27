#!./venv/Scripts/python3

from os import environ as os_environ
from os import remove as os_remove
from multiprocessing import Process
from sys import argv
from function_manage import main
from copy import deepcopy

# from pathing_info import python_env, manage
# from server_config import background_sleep_time as delay

arg_p = deepcopy(argv)
arg_np = deepcopy(argv)
arg_db_clean = deepcopy(argv)
os_environ['PYTHONUNBUFFERED'] = "1"

# arg_task = [python_env, manage, 'process_tasks', '--log-std', '--sleep', str(delay)]

if __name__ == '__main__':

    delete_after = False
    try:
        import db_config
    except ImportError:
        db_config_file = open("db_config.py", "w+")
        db_config_file.write("DATABASES = {\n"
                             "    'default': {\n"
                             "        'ENGINE': 'django.db.backends.postgresql_psycopg2',\n"
                             "        'NAME': 'armstestdb',\n"
                             "        'USER': 'armstestuser',\n"
                             "        'PASSWORD': 'atu-Passwd-123',\n"
                             "        'HOST': 'test-postgres-db.teamcity.dev.kobil.com',\n"
                             "        'PORT': '5432',\n"
                             "    }\n"
                             "}\n"
                             "")
        db_config_file.close()
        delete_after = True

    def my_exit(exit_code: int = 0):
        if delete_after:
            os_remove("db_config.py")
        exit(exit_code)

    # parallel test definition
    arg_p.append("test")
    arg_p.append("--noinput")
    arg_p.append("--failfast")
    arg_p.append("--parallel")
    arg_p.append("--exclude-tag")
    arg_p.append("non-parallel")

    # sequential test definition
    arg_np.append("test")
    arg_np.append("--noinput")
    arg_np.append("--failfast")
    arg_np.append("--tag")
    arg_np.append("non-parallel")
    arg_np.append("--keepdb")

    # runs 1 test to clean the db
    arg_db_clean.append("test")
    arg_db_clean.append("--parallel")
    arg_db_clean.append("--noinput")
    arg_db_clean.append("devices.tests.StaticValTests.test_devices_put")

    pp = Process(target=main, args=arg_p)
    pp.start()
    pp.join()

    if pp.exitcode > 0:
        my_exit(pp.exitcode)

    np = Process(target=main, args=arg_np)
    np.start()
    np.join()

    dbc = Process(target=main, args=arg_db_clean)
    dbc.start()
    dbc.join()

    if np.exitcode > 0:
        my_exit(np.exitcode)
    # else
    my_exit(0)
