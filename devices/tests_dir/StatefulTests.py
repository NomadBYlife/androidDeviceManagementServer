from json import JSONEncoder
from threading import Barrier
from multiprocessing.pool import ThreadPool

from django.test import Client
from django.test import TestCase, LiveServerTestCase
from django.http import JsonResponse, HttpResponse

from devices.models import Device, DeviceType, DeviceFunction
from devices.common.functions import get_dict_from_model
from devices.tests_dir.common.decorators import do_rest_json, do_rest_http

from devices.tests_dir.common.functions import make_devices, make_function
from devices.tests_dir.common.fixtures import default_devices, \
    cla_device, res_fail_fun_device, off_device, res_device
from devices.common.functions import safe_delete_all

from log_config import set_log_level

log = set_log_level()
c = Client()
enc = JSONEncoder().encode


class StatefulTests(TestCase):
    def __init__(self, *args, **kwargs):
        super(StatefulTests, self).__init__(*args, **kwargs)

    def tearDown(self):
        safe_delete_all(DeviceFunction)
        safe_delete_all(Device)
        safe_delete_all(DeviceType)

    # '/devices/claim/<device_type>/'

    @make_devices(default_devices())
    @do_rest_http(c.get, "/devices/claim/%s/" % default_devices()[0]['type'])
    def test_devices_claim_get_pos(self, response: HttpResponse, **kwargs):
        # checks response status code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase, "OK")
        # checks response cmd stdout
        self.assertEqual(response.content.decode(),
                         "%s:%s" % (default_devices()[0]['ip'], default_devices()[0]['port']))
        # checks database changes
        device: dict = default_devices()[0]
        device.update(**{'owner': '127.0.0.1', 'allocated': True})
        db_device_list = get_dict_from_model(Device)
        self.assertEqual(device, db_device_list[default_devices()[0]['key']])

    @make_devices(res_device())
    @do_rest_http(c.get, "/devices/claim/%s/" % res_device()[0]['type'])
    def test_devices_claim_get_neg_res(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.reason_phrase, "Conflict")
        self.assertEqual(response.content.decode(), "Retry in a few seconds")

    @make_devices(off_device())
    @do_rest_http(c.get, "/devices/claim/%s/" % off_device()[0]['type'])
    def test_devices_claim_get_neg_off(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.reason_phrase, "Service Unavailable")
        self.assertEqual(response.content.decode(),
                         "No device of type '%s' unclaimed, enabled and on" % off_device()[0]['type'])

    # '/devices/release/<device_key>/'

    @make_devices(cla_device())
    @do_rest_json(c.get, "/devices/release/%s/" % cla_device()[0]['key'])
    def test_devices_release_get_pos(self, response: JsonResponse, body: dict, **kwargs):
        device: dict = cla_device()[0]
        device.update(**{'owner': None, 'allocated': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase, "OK")
        self.maxDiff = None
        self.assertDictEqual(body, device)

    @make_devices(res_fail_fun_device())
    @make_function('restart', res_fail_fun_device()[0]['type'])
    @do_rest_json(c.get, "/devices/release/%s/" % res_fail_fun_device()[0]['key'])
    def test_devices_release_get_pos_fail_restart(self, response: JsonResponse, body: dict, **kwargs):
        device_dict: dict = res_fail_fun_device()[0]
        device_dict.update(**{'owner': None, 'allocated': False, 'status': 'ON'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase, "OK")
        self.assertDictEqual(body, device_dict)

    # '/devices/functions/<function_name>/<device_key>/'

    # @make_devices()
    # def test_devices_function_get_pos_restart(self, ...):


class ConcurrentStatefulTests(LiveServerTestCase):
    log = set_log_level()

    def tearDown(self):
        safe_delete_all(DeviceFunction)
        safe_delete_all(Device)
        safe_delete_all(DeviceType)

    @make_devices(default_devices(3))
    def test_devices_claim_concurrency(self, **kwargs):
        sync_gate: Barrier = Barrier(3)

        def do_claim() -> str:
            sync_gate.wait()
            response: HttpResponse = c.get("/devices/claim/%s/" % default_devices()[0]['type'])
            return response.content.decode()

        thread_pool: ThreadPool = ThreadPool(processes=3)
        for iterations in range(0, 1):
            future1 = thread_pool.apply_async(do_claim)
            future2 = thread_pool.apply_async(do_claim)
            future3 = thread_pool.apply_async(do_claim)

            result1: str = future1.get()
            result2: str = future2.get()
            result3: str = future3.get()

            def the_fail():
                self.fail("Two claims got same device. Think more about concurrency")

            if result1 == result2:
                the_fail()
            if result1 == result3:
                the_fail()
            if result2 == result3:
                the_fail()

            sync_gate.reset()
