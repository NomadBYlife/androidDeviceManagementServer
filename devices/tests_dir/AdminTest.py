import os
import threading

from copy import deepcopy
from os import environ as os_environ
from typing import Union
from time import sleep
from datetime import datetime, timezone
from unittest import skipUnless

from django.test import tag
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

from background_task.models_completed import CompletedTask

from devices.models import Device, DeviceType, DeviceFunction
from devices.tests_dir.common.functions import pretty_string_debug_template_response, make_path_to_function_script
from devices.common.functions import safe_get_model_all, safe_get_model_by, safe_delete_all, safe_create, \
    safe_create_superuser, safe_delete_instance
from devices.tests_dir.common.fixtures import real_emu

from log_config import set_log_level

log = set_log_level()
adms_run_integration: bool = False
if os_environ.get('ADMS_RUN_INTEGRATION') is not None:
    adms_run_integration: bool = True


def default_tear_down():
    safe_delete_all(User)
    safe_delete_all(DeviceFunction)
    safe_delete_all(Device)
    safe_delete_all(DeviceType)


def user_setup(self):
    user: User = safe_create_superuser(username='test', password='test', email='test@test.test')
    self.client.force_login(user)
    return user


def device_type_setup(type_name) -> DeviceType:
    return safe_create(DeviceType, type_def=type_name)


def device_type_dict_setup(type_name) -> (dict, dict):
    type_dict: dict = {'type_def': type_name}
    type_dict_ex: dict = deepcopy(type_dict)
    return type_dict, type_dict_ex


default_device_dict: dict = {'ip': '1.2.3.4', 'port': 1234,
                             'type': 'type-0', 'description': 'desc-0',
                             'status': 'ON', 'enabled': True,
                             'owner': '', 'allocated': False,
                             'key': '1.2.3.4-1234', 'priority': 9999}


def device_setup(device_type: DeviceType, **changes) -> Device:
    device_dict: dict = deepcopy(default_device_dict)
    device_dict.update({'type': device_type})
    device_dict.update(**changes)
    return safe_create(Device, **device_dict)


def device_dict_setup(**changes) -> (dict, dict):
    device_dict: dict = deepcopy(default_device_dict)
    device_dict.update(**changes)
    device_dict_ex: dict = deepcopy(device_dict)
    device_dict_ex.update({'owner': None})
    return device_dict, device_dict_ex


default_action_dict: dict = {'action': 'delete_selected',
                             '_selected_action': [],
                             'post': 'yes'}


def action_setup(thing, pos: int = 0, **changes) -> dict:
    all_things = safe_get_model_all(thing)
    action_dict: dict = deepcopy(default_action_dict)
    action_dict.update({'_selected_action': all_things[pos].pk})
    action_dict.update(**changes)
    return action_dict


def device_function_setup(fun_name: str, for_type: str) -> DeviceFunction:
    device_type: DeviceType = safe_get_model_by(DeviceType, type_def=for_type)
    device_function_dict: dict = {'function_name': fun_name,
                                  'type_association': device_type}
    return safe_create(DeviceFunction, **device_function_dict)


def device_function_dict_setup(fun_name: str, for_type: str, **changes) -> (dict, dict):
    device_function_dict: dict = {'function_name': fun_name, 'type_association': for_type}
    device_function_dict.update(**changes)
    device_function_dict_ex: dict = deepcopy(device_function_dict)
    device_function_dict_ex.update({'type_association': for_type})
    device_function_dict_ex.update({'key': "%s-%s" % (for_type, fun_name)})
    device_function_dict_ex.update({'script_found': False})
    device_function_dict_ex.update(
        {'script_path': make_path_to_function_script(for_type, fun_name)})
    return device_function_dict, device_function_dict_ex


def verb_template_response(self, verb: str, url: str, data: dict = None) -> (TemplateResponse, bool):
    def get_verb_function(i_verb: str):
        verb_map = {
            'get': self.client.get,
            'post': self.client.post
        }
        return verb_map.get(i_verb)

    verb_function = get_verb_function(verb)

    response: Union[HttpResponseRedirect, TemplateResponse] = verb_function(url, data)
    followed: bool = False
    if type(response) is HttpResponseRedirect:
        response: Union[HttpResponseRedirect, TemplateResponse] = verb_function(response.url, data, follow=True)
        followed: bool = True
    if type(response) is not TemplateResponse:
        self.fail(pretty_string_debug_template_response(response))  # pragma: no cover
    # else
    return response, followed


def check_response(self, response: TemplateResponse, followed: bool,
                   followed_expected: bool = True, response_code_expected: int = 200):
    self.assertEqual(response.status_code, response_code_expected)
    self.assertEqual(followed, followed_expected, pretty_string_debug_template_response(response))


def check_object(self, thing, thing_dict: dict, len_expected: int = 2, pos_expected: int = 1):
    all_objects = list(safe_get_model_all(thing))
    self.assertEqual(len(all_objects), len_expected, str(all_objects))
    self.maxDiff = None
    self.assertDictEqual(all_objects[pos_expected].as_dict(), thing_dict)
    return all_objects[pos_expected].as_dict()


def check_error(self, response, str_expected: str, add_class: str = " nonfield"):
    self.assertContains(response, 'Please correct the error below.',
                        msg_prefix=pretty_string_debug_template_response(response))
    self.assertContains(response, "<ul class=\"errorlist%s\"><li>%s</li></ul>" % (add_class, str_expected),
                        msg_prefix=pretty_string_debug_template_response(response))


def check_action(self, response, str_expected: str):
    self.assertContains(response, "<li class=\"success\">%s</li>" % str_expected,
                        msg_prefix=pretty_string_debug_template_response(response))


class AdminTestViews(TestCase):
    def setUp(self):
        self.type_name: str = 'type-0'
        self.ip: str = '1.2.3.4'
        self.port: int = 1234
        self.fun_name: str = 'restart'
        self.fun_dne: str = 'DNE'
        self.user = user_setup(self)
        self.device_type_dict, self.device_type_dict_ex = device_type_dict_setup(self.type_name)
        self.device_dict, self.device_dict_ex = device_dict_setup()
        self.device_fun_dict, self.device_fun_dict_ex = device_function_dict_setup(self.fun_name, self.type_name)
        self.device_fun_dne, self.device_fun_dne_ex = device_function_dict_setup(self.fun_dne, self.type_name)

    def tearDown(self):
        default_tear_down()

    def view_gen_pos(self, url: str):
        self.device_type = device_type_setup(self.type_name)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_setup(self.device_type)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_function_setup(self.fun_name, self.type_name)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_function_setup(self.fun_dne, self.type_name)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_type: DeviceType = safe_get_model_by(DeviceType, type_def=self.type_name)
        safe_delete_instance(DeviceType, device_type.pk)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

    def test_view_device_pos(self):
        self.view_gen_pos('/admin/devices/device/')

    def test_view_function_pos(self):
        self.view_gen_pos('/admin/devices/devicefunction/')

    def test_view_types_pos(self):
        self.view_gen_pos('/admin/devices/devicetype/')

    def view_gen_device_pos(self, url: str):
        self.device_type = device_type_setup(self.type_name)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed)

        device_setup(self.device_type)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_function_setup(self.fun_name, self.type_name)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_function_setup(self.fun_dne, self.type_name)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

        device_type: DeviceType = safe_get_model_by(DeviceType, type_def=self.type_name)
        safe_delete_instance(DeviceType, device_type.pk)
        response, followed = verb_template_response(self, 'get', url)
        check_response(self, response, followed, False)

    def test_view_device_change_pos(self):
        self.view_gen_device_pos("/admin/devices/device/%s-%s/change/" % (self.ip, self.port))

    def view_gen_functions_pos(self, url: callable):
        self.device_type = device_type_setup(self.type_name)
        response, followed = verb_template_response(self, 'get', url())
        check_response(self, response, followed)

        device_function_setup(self.fun_name, self.type_name)
        response, followed = verb_template_response(self, 'get', url())
        check_response(self, response, followed, False)

        device_setup(self.device_type)
        response, followed = verb_template_response(self, 'get', url())
        check_response(self, response, followed, False)

        device_function_setup(self.fun_dne, self.type_name)
        response, followed = verb_template_response(self, 'get', url())
        check_response(self, response, followed, False)

        device_type: DeviceType = safe_get_model_by(DeviceType, type_def=self.type_name)
        safe_delete_instance(DeviceType, device_type.pk)
        response, followed = verb_template_response(self, 'get', url(None, self.fun_name))
        check_response(self, response, followed, False)

    def test_view_gen_function_change_pos(self):
        def get_url(type_name: str = self.type_name, fun_name: str = self.fun_name):
            return "/admin/devices/devicefunction/%s-%s/change/" % (type_name, fun_name)

        self.view_gen_functions_pos(get_url)


class AdminTestDeviceAdd(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'
        self.ex_ip: str = '2.3.4.5'
        self.ip: str = '1.2.3.4'
        self.ex_port: int = 2345
        self.port: int = 1234

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.device_dict, self.device_dict_ex = device_dict_setup()
        self.device = device_setup(self.device_type, **{'ip': self.ex_ip, 'port': self.ex_port})

    def tearDown(self):
        default_tear_down()

    def test_add_device_pos(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex)

    def test_add_device_pos_type_none(self):
        self.device_dict.update({'type': ''})
        self.device_dict_ex.update({'type': 'None'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex)

    def test_add_device_neg_duplicate(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device.as_dict())
        check_response(self, response, followed, False)
        check_error(self, response, "Combination of ip and port: %s:%s is not unique" % (self.ex_ip, self.ex_port))

    def test_add_device_neg_bad_ip(self):
        self.device_dict.update({'ip': '1.2.34'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid IPv4 or IPv6 address.", "")

    def test_add_device_neg_bad_port_outside_low(self):
        self.add_device_neg_bad_port_outside(1000)

    def test_add_device_neg_bad_port_outside_high(self):
        self.add_device_neg_bad_port_outside(65536)

    def test_add_device_pow_port_inside_low(self):
        self.add_device_pos_port_inside(1001)

    def test_add_device_pos_port_inside_high(self):
        self.add_device_pos_port_inside(65535)

    def add_device_pos_port_inside(self, port: int):
        self.device_dict.update({'port': port})
        self.device_dict_ex.update({'port': port, 'key': "%s-%s" % (self.ip, port)})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex)

    def add_device_neg_bad_port_outside(self, port: int):
        self.device_dict.update({'port': port})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "%s outside of port range 1001-65535" % port, "")

    def test_add_device_neg_bad_type(self):
        self.device_dict.update({'type': 'DNE'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Select a valid choice. That choice is not one of the available choices.", "")

    def test_add_device_neg_bad_desc(self):
        self.device_dict.update({'description': 'as*df'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid &#39;slug&#39; consisting of letters, numbers, underscores or "
                                    "hyphens.", "")

    def test_add_device_neg_bad_status(self):
        # TODO check all known stati - do this to make breaking api changes obvious
        status: str = 'DNE'
        self.device_dict.update({'status': status})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Select a valid choice. %s is not one of the available choices." % status, "")

    def test_add_device_neg_bad_owner(self):
        # TODO check what happens when a host is known by url and we get the dns name
        owner = "None"
        self.device_dict.update({'owner': owner})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/add/', self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid IPv4 or IPv6 address.", "")


class AdminTestDeviceChange(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'
        self.ex_ip: str = '1.2.3.4'
        self.ip: str = '1.2.3.5'
        self.ex_port: int = 1234
        self.port: int = 1235

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.device_dict, self.device_dict_ex = device_dict_setup()
        self.device = device_setup(self.device_type)

    def tearDown(self):
        default_tear_down()

    def test_trigger_notification_cleared(self):
        safe_create(CompletedTask, run_at=datetime.now(timezone.utc))
        self.device_dict_ex.update({'ip': self.ip, 'key': "%s-%s" % (self.ip, self.ex_port)})
        self.device_dict.update({'ip': self.ip})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_ip(self):
        self.device_dict_ex.update({'ip': self.ip, 'key': "%s-%s" % (self.ip, self.ex_port)})
        self.device_dict.update({'ip': self.ip})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_port(self):
        self.device_dict.update({'port': self.port})
        self.device_dict_ex.update({'port': self.port, 'key': "%s-%s" % (self.ex_ip, self.port)})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_desc(self):
        self.device_dict_ex.update({'description': 'desc-1'})
        self.device_dict.update({'description': 'desc-1'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_status(self):
        self.device_dict_ex.update({'status': 'OFF'})
        self.device_dict.update({'status': 'OFF'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_enabled(self):
        self.device_dict_ex.update({'enabled': True})
        self.device_dict.update({'enabled': True})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_owner(self):
        self.device_dict_ex.update({'owner': '2.3.4.5'})
        self.device_dict.update({'owner': '2.3.4.5'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_pos_allocated(self):
        self.device_dict_ex.update({'allocated': True})
        self.device_dict.update({'allocated': True})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_change_device_neg_ip(self):
        self.device_dict.update({'ip': '1.2.35'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/%s-%s/change/' %
                                                    (self.ex_ip, self.ex_port), self.device_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid IPv4 or IPv6 address.", "")


class AdminTestDeviceDelete(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.device = device_setup(self.device_type)
        self.action_dict = action_setup(Device)

    def tearDown(self):
        default_tear_down()

    def test_delete_device_pos(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/device/', self.action_dict)
        check_response(self, response, followed)
        check_action(self, response, "Successfully deleted 1 device.")
        self.assertEqual(len(safe_get_model_all(Device)), 0)


class AdminTestDeviceTypeAdd(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'

        self.user = user_setup(self)
        self.device_type_dict, self.device_type_dict_ex = device_type_dict_setup(self.ex_type_name)

    def tearDown(self):
        default_tear_down()

    # TODO check if we get race conditions with our current setup if we have more than 1 pos test creating device types
    def test_add_type_pos(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicetype/add/',
                                                    self.device_type_dict)
        check_response(self, response, followed)
        check_object(self, DeviceType, self.device_type_dict_ex, 1, 0)

    def test_add_type_neg_non_slug(self):
        self.device_type_dict.update({'type_def': 'as*df'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicetype/add/',
                                                    self.device_type_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid &#39;slug&#39; consisting of letters, numbers, underscores or "
                                    "hyphens.", "")


class AdminTestDeviceTypeChange(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'
        self.type_name: str = 'type-1'

        self.user = user_setup(self)
        device_type: DeviceType = device_type_setup(self.ex_type_name)
        self.device_type_id: int = device_type.pk

        device: Device = device_setup(device_type)
        device_dict, self.device_dict_ex = device_dict_setup(**{'type': self.type_name})

        device_function_setup('func-0', self.ex_type_name)
        device_function_dict, self.device_function_dict_ex = device_function_dict_setup('func-0', self.type_name)

        self.device_type_dict, self.device_type_dict_ex = device_type_dict_setup(self.ex_type_name)

    def tearDown(self):
        default_tear_down()

    def test_change_type_pos(self):
        self.device_type_dict_ex.update({'type_def': self.type_name})
        self.device_type_dict.update({'type_def': self.type_name})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicetype/%s/change/'
                                                    % self.device_type_id, self.device_type_dict)
        check_response(self, response, followed)
        check_object(self, DeviceType, self.device_type_dict_ex, 1, 0)
        check_object(self, Device, self.device_dict_ex, 1, 0)
        check_object(self, DeviceFunction, self.device_function_dict_ex, 1, 0)

    def test_change_type_neg_non_slug(self):
        self.device_type_dict.update({'type_def': 'as*df'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicetype/%s/change/'
                                                    % self.device_type_id, self.device_type_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid &#39;slug&#39; consisting of letters, numbers, underscores or "
                                    "hyphens.", "")


class AdminTestDeviceTypeDelete(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.action_dict = action_setup(DeviceType)

    def tearDown(self):
        default_tear_down()

    def test_delete_type_pos(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicetype/', self.action_dict)
        check_response(self, response, followed)
        check_action(self, response, "Successfully deleted 1 device type.")
        self.assertEqual(len(safe_get_model_all(DeviceType)), 0)


class AdminTestDeviceFunctionAdd(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'
        self.fun_name: str = 'first'
        self.ex_fun_name: str = 'second'

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.device = device_setup(self.device_type)
        self.device_function_dict, self.device_function_dict_ex = \
            device_function_dict_setup(self.fun_name, self.ex_type_name)
        self.device_function = device_function_setup(self.ex_fun_name, self.ex_type_name)

    def tearDown(self):
        default_tear_down()

    def test_add_function_pos(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicefunction/add/',
                                                    self.device_function_dict)
        check_response(self, response, followed)
        check_object(self, DeviceFunction, self.device_function_dict_ex)

    def test_add_function_pos_dne(self):
        local_name: str = 'DNE'
        self.device_function_dict_ex.update(
            {'function_name': local_name,
             'key': '%s-%s' % (self.ex_type_name, local_name),
             'script_found': False,
             'script_path': make_path_to_function_script('type-0', local_name)})
        self.device_function_dict.update({'function_name': local_name})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicefunction/add/',
                                                    self.device_function_dict)
        check_response(self, response, followed)
        check_object(self, DeviceFunction, self.device_function_dict_ex)

    def test_add_function_neg_duplicate(self):
        self.device_function_dict.update({'function_name': self.ex_fun_name})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicefunction/add/',
                                                    self.device_function_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Combination of type and name: %s-%s is not unique" %
                    (self.ex_type_name, self.ex_fun_name))


class AdminTestDeviceFunctionChange(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'
        self.ex_type_name_other: str = 'type-1'
        self.ex_fun_name: str = 'first'
        self.ex_fun_name_other: str = 'second'

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.device_type_other = device_type_setup(self.ex_type_name_other)
        self.device_function = device_function_setup(self.ex_fun_name, self.ex_type_name)
        self.device_function_dict, self.device_function_dict_ex = \
            device_function_dict_setup(self.ex_fun_name, self.ex_type_name)

    def tearDown(self):
        default_tear_down()

    # TODO wirte a test which creates a function then creates the script after the function was added and check if its
    #  existance status changes when the page is refresh or something

    def test_change_function_pos(self):
        self.device_function_dict_ex.update({})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicefunction/%s-%s/change/' %
                                                    (self.ex_type_name, self.ex_fun_name), self.device_function_dict)
        check_response(self, response, followed)
        check_object(self, DeviceFunction, self.device_function_dict_ex, 1, 0)

    def test_change_function_neg_non_slug(self):
        self.device_function_dict.update({'function_name': 'as*df'})
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicefunction/%s-%s/change/' %
                                                    (self.ex_type_name, self.ex_fun_name), self.device_function_dict)
        check_response(self, response, followed, False)
        check_error(self, response, "Enter a valid &#39;slug&#39; consisting of letters, numbers, underscores or "
                                    "hyphens.", "")


class AdminTestDeviceFunctionDelete(TestCase):
    def setUp(self):
        self.ex_type_name: str = 'type-0'
        self.ex_fun_name: str = 'first'

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        self.device_function = device_function_setup(self.ex_fun_name, self.ex_type_name)
        self.action_dict = action_setup(DeviceFunction)

    def tearDown(self):
        default_tear_down()

    def test_delete_function_pos(self):
        response, followed = verb_template_response(self, 'post', '/admin/devices/devicefunction/', self.action_dict)
        check_response(self, response, followed)
        check_action(self, response, "Successfully deleted 1 device function.")
        self.assertEqual(len(safe_get_model_all(DeviceFunction)), 0)


class AdminTestDeviceFunctionDo(TransactionTestCase):
    def setUp(self):
        # the 'unused' data points here cause a lot branches to be traversed during test execution
        # which may other wise not be executed
        self.ex_type_name: str = 'type-0'
        self.ex_type_name_other: str = 'type-1'
        self.ex_fun_name: str = 'check_status'
        self.ex_fun_name_2: str = 'restart'
        self.ex_fun_name_other: str = 'other'
        self.ex_fun_name_dne_other: str = 'DNE_other'

        self.ex_ip: str = '1.2.3.4'
        self.ex_port: int = 1234

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.ex_type_name)
        device_type_setup(self.ex_type_name_other)
        self.device = device_setup(self.device_type)
        self.device_dict, self.device_dict_ex = device_dict_setup()
        device_function_setup(self.ex_fun_name, self.ex_type_name)
        device_function_setup(self.ex_fun_name_2, self.ex_type_name)
        device_function_setup(self.ex_fun_name_other, self.ex_type_name_other)
        device_function_setup(self.ex_fun_name_dne_other, self.ex_type_name_other)
        self.device_dict_ex.update({'status': 'ON'})

    def tearDown(self):
        default_tear_down()

    def test_do_function_pos(self):
        response, followed = verb_template_response(self, 'get', '/admin/devices/device/function/%s-%s/%s/' %
                                                    (self.ex_ip, self.ex_port, self.ex_fun_name))
        check_response(self, response, followed)
        sleep(0.5)
        check_object(self, Device, self.device_dict_ex, 1, 0)

    def test_do_function_pos_restart(self):
        self.device_dict_ex.update({'status': 'RES'})
        response, followed = verb_template_response(self, 'get', '/admin/devices/device/function/%s-%s/%s/' %
                                                    (self.ex_ip, self.ex_port, self.ex_fun_name_2))
        check_response(self, response, followed)
        sleep(0.5)
        check_object(self, Device, self.device_dict_ex, 1, 0)


@tag('non-parallel')
@skipUnless(adms_run_integration, "uses active emulators, integration test")
class AdminTestIntegration(TransactionTestCase):
    def setUp(self):
        log.debug("            dbg - set up")
        self.type_name: str = real_emu()[0]['type']
        self.ip: str = real_emu()[0]['ip']
        self.port: int = real_emu()[0]['port']

        self.check_lock: str = 'check_status'
        self.restart: str = 'restart'

        self.user = user_setup(self)
        self.device_type = device_type_setup(self.type_name)
        self.device = device_setup(self.device_type, **{'ip': self.ip, 'port': self.port})
        self.device_dict, self.device_dict_ex = device_dict_setup(**(real_emu()[0]))
        device_function_setup(self.check_lock, self.type_name)
        device_function_setup(self.restart, self.type_name)
        self.device_dict_ex.update({'status': 'ON'})

    def tearDown(self):
        log.debug("          dbg - tear down")
        default_tear_down()

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    def test_do_unlocked_after_restart(self):
        log.debug('    dbg - test checks - test_client_adc_claim_pos')
        verb_template_response(self, 'get', '/admin/devices/device/function/%s-%s/%s/' %
                               (self.ip, self.port, self.restart))
        log.debug("          dbg - func > check")
        sleep(180)
        response, followed = verb_template_response(self, 'get', '/admin/devices/device/function/%s-%s/%s/' %
                                                    (self.ip, self.port, self.check_lock))
        log.debug("          dbg - check > default checks")
        check_response(self, response, followed)
        check_object(self, Device, self.device_dict_ex, 1, 0)
