import logging
from json import JSONEncoder

from django.test import Client
from django.test import TestCase
from django.http import JsonResponse, HttpResponse

from devices.models import Device, DeviceType
from devices.common.functions import get_dict_from_model
from devices.tests_dir.common.decorators import do_rest_json, do_rest_http
from devices.common.functions import safe_get_model_all, safe_create, safe_delete_all

from log_config import set_log_level

log = set_log_level()
c = Client()
enc = JSONEncoder().encode


class StaticValTests(TestCase):
    def __init__(self, *args, **kwargs):
        super(StaticValTests, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        type_0 = safe_create(DeviceType, type_def="type-0")
        type_1 = safe_create(DeviceType, type_def="type-1")
        safe_create(Device, ip="1.2.3.4", port="1234", type=type_0, description="desc-0", status="ON",
                    enabled=True, owner=None, allocated=False, key="1.2.3.4-1234")
        safe_create(Device, ip="2.3.4.5", port="2345", type=type_0, description="desc-1", status="---",
                    enabled=False, owner="1.1.1.1", allocated=True, key="2.3.4.5-2345")
        safe_create(Device, ip="3.4.5.6", port="3456", type=type_1, description="desc-0", status="---",
                    enabled=False, owner=None, allocated=False, key="3.4.5.6-3456")
        safe_create(Device, ip="4.5.6.7", port="4567", type=type_1, description="desc-1", status="---",
                    enabled=True, owner="2.2.2.2", allocated=True, key="4.5.6.7-4567")

    @classmethod
    def tearDownClass(cls):
        safe_delete_all(Device)
        safe_delete_all(DeviceType)

    # '/devices/'

    @do_rest_json(c.get, '/devices/')
    def test_devices_get_pos(self, response: JsonResponse, body: dict, **kwargs):
        device_list = get_dict_from_model(Device)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase, "OK")
        self.assertDictEqual(body, device_list)

    @do_rest_http(c.put, '/devices/')
    def test_devices_put(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.post, '/devices/')
    def test_devices_post(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.delete, '/devices/')
    def test_devices_delete(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    # '/devices/<int>/'

    @do_rest_json(c.get, '/devices/detail/1.2.3.4-1234/')
    def test_devices_1_get_pos(self, response: JsonResponse, body: dict, **kwargs):
        device_list = get_dict_from_model(Device)
        device: dict = device_list['1.2.3.4-1234']
        device.update({'key': '1.2.3.4-1234'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase, "OK")
        self.assertDictEqual(body, device)

    @do_rest_json(c.get, '/devices/detail/DNE/')
    def test_devices_get_neg_key_dne(self, response: JsonResponse, body: dict, **kwargs):
        rep_dict: dict = {'Error': "Device 'DNE' does not exist"}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase, "Not Found")
        self.assertDictEqual(body, rep_dict)

    @do_rest_http(c.put, '/devices/detail/1.2.3.4-1234/')
    def test_devices_1_put(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.post, '/devices/detail/1.2.3.4-1234/')
    def test_devices_1_post(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.delete, '/devices/detail/1.2.3.4-1234/')
    def test_devices_1_delete(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    # '/devices/claim/<device_type>/'

    @do_rest_http(c.get, '/devices/claim/-INVALID-/')
    def test_devices_claim_get_neg_inv_type(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase, "Bad Request")
        self.assertEqual(response.content.decode(), "Device type '-INVALID-' unknown")

    @do_rest_http(c.get, '/devices/claim/type-1/')
    def test_devices_claim_get_neg_unavailable(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.reason_phrase, "Service Unavailable")
        # TODO extract crap strings
        self.assertEqual(response.content.decode(), "No device of type 'type-1' unclaimed, enabled and on")

    @do_rest_http(c.put, '/devices/claim/type-0/')
    def test_devices_claim_put(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.post, '/devices/claim/type-0/')
    def test_devices_claim_post(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.delete, '/devices/claim/type-0/')
    def test_devices_claim_delete(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    # '/devices/release/'

    @do_rest_http(c.put, '/devices/release/ignored/')
    def test_devices_release_put(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.post, '/devices/release/ignored/')
    def test_devices_release_post(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.delete, '/devices/release/ignored/')
    def test_devices_release_delete(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.reason_phrase, "Method Not Allowed")

    @do_rest_http(c.get, '/devices/release/')
    def test_devices_release_get_neg_key_missing(self, response: HttpResponse, **kwargs):
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase, "Not Found")

    @do_rest_json(c.get, '/devices/release/DNE/')
    def test_devices_release_get_neg_key_dne(self, response: JsonResponse, body: dict, **kwargs):
        expected: dict = {"Error": "Device 'DNE' does not exist"}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase, "Not Found")
        self.assertDictEqual(body, expected)

    @do_rest_json(c.get, '/devices/release/1.2.3.4-1234/')
    def test_devices_release_get_pos_ntd(self, response: JsonResponse, body: dict, **kwargs):
        device_list = get_dict_from_model(Device)
        device: dict = device_list['1.2.3.4-1234']
        device.update({'key': '1.2.3.4-1234'})
        device.update({"allocated": False, "owner": None})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase, "OK")
        self.assertDictEqual(body, device)
