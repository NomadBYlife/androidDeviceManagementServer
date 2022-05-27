from os import path
from json import JSONDecoder

from django.template.response import TemplateResponse

from devices.models import Device, DeviceType, DeviceFunction
from devices.common.functions import safe_get_model_by, safe_create

from pathing_info import basedir

from log_config import set_log_level

log = set_log_level()


def make_path_to_function_script(type_name: str, fun_name: str) -> str:
    return path.join(basedir, 'devices', 'function_dir', type_name, "%s.sh" % fun_name)


def pretty_string_debug_template_response(response: TemplateResponse) -> str:
    res_string: str = response.rendered_content.strip()
    no_empties: str = ''
    for line in res_string.split('\n'):
        if line.strip():
            no_empties += line
            no_empties += '\n'
    return no_empties


# check functions

def check_exit_code(self, expected_exit_code: int, **kwargs):
    self.assertEqual(expected_exit_code, kwargs.get('exit_code'),
                     msg="\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %
                         (kwargs.get('stderr'), kwargs.get('stdout')))


def check_stderr_for(self, expected_string: str, **kwargs):
    if expected_string not in kwargs.get('stderr'):
        self.fail("%s not found in stderr\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                  (expected_string, kwargs.get('stderr'), kwargs.get('stdout')))


def check_stderr_not(self, not_expected_string: str, **kwargs):  # might not need this function
    if not_expected_string in kwargs.get('stderr'):  # future use? # pragma: no cover
        self.fail("%s not found in stderr\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                  (not_expected_string, kwargs.get('stderr'), kwargs.get('stdout')))


def check_stdout_for_dict(self, expected_dict: dict, line: int = 0, **kwargs):
    dict_from_str: dict = JSONDecoder().decode(kwargs.get('stdout').split('\n')[line])
    self.maxDiff = None
    self.assertDictEqual(expected_dict, dict_from_str)


def check_stdout_dict_for(self, expected_key: str, expected_val, **kwargs):  # unused test code # pragma: no cover
    list_of_string_dicts: list = kwargs.get('stdout').split('\n')
    dict_list: list = []
    for string_dict in list_of_string_dicts:
        dict_list.append(JSONDecoder().decode(string_dict))
    self.maxDiff = None
    for single_dict in dict_list:
        if expected_key in single_dict.keys():
            if expected_val == single_dict[expected_key]:
                return
    # string not found
    self.fail("%s NOT found in stdout\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
              (expected_val, kwargs.get('stdout')))


def check_stdout_for(self, expected_string: str, line: int = 0, **kwargs):
    if expected_string not in kwargs.get('stdout').split('\n')[line]:
        self.fail("%s not equal stdout\n  ---  STDOUT  ---\n%s" %  # pragma no cover
                  (expected_string, kwargs.get('stdout')))


def check_stdout_for_any_line(self, expected_string: str, **kwargs):
    for line in kwargs.get('stdout').split('\n'):
        if expected_string in line:
            return
    self.fail("%s not found in stdout\n  ---  STDOUT  ---\n%s" %  # pragma no cover
              (expected_string, kwargs.get('stdout')))


def check_stdout_not(self, not_expected_string: str, **kwargs):
    for string in kwargs.get('stdout').split('\n'):
        if not_expected_string in string:
            self.fail("%s FOUND! in stdout\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                      (not_expected_string, kwargs.get('stdout')))


# setup functions

def __make_type(i_type_def: str):  # test setup code # pra-break-gma: no cover
    # noinspection PyUnresolvedReferences
    try:
        device_type: DeviceType = safe_get_model_by(DeviceType, type_def=i_type_def)
    except DeviceType.DoesNotExist:
        device_type: DeviceType = safe_create(DeviceType, type_def=i_type_def)
    return device_type


def make_type(i_type_def: str):  # test setup code # pra-break-gma: no cover
    def decorator(fun):
        def wrapper(*args, **kwargs):
            __make_type(i_type_def)
            ret_val = fun(*args, **kwargs)
            return ret_val

        return wrapper

    return decorator


def make_devices(i_device_list: list):  # test setup code # pra-break-gma: no cover
    def decorator(fun):
        def wrapper(*args, **kwargs):
            for device_kwargs in i_device_list:
                type_def = device_kwargs.pop('type')
                device_type = __make_type(type_def)
                safe_create(Device, **{'type': device_type, **device_kwargs})
            ret_val = fun(*args, **kwargs)
            return ret_val

        return wrapper

    return decorator


def make_function(func_name, type_def):  # test setup code # pra-break-gma: no cover
    def decorator(fun):
        def wrapper(*args, **kwargs):
            device_type = __make_type(type_def)
            safe_create(DeviceFunction, type_association=device_type, function_name=func_name)
            ret_val = fun(*args, **kwargs)
            return ret_val

        return wrapper

    return decorator
