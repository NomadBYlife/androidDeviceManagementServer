import logging
from copy import deepcopy
from typing import Union, Tuple
from enum import Enum

from django.http import HttpRequest, HttpResponse
from django.db import transaction

from devices.views_dir.common.functions import find_device_by_list, check_device_type_exists
from devices.model_dir.Devices import Device
from devices.views_dir.common.logging import log_request

log = logging.getLogger('adms.views')


class ClaimFailure(Enum):
    wait = 0
    retry = 1
    fail = 2


# this function can produce 4 results
# 1 it claims a device and returns a device
#       'ok': atom, device: Device
# 2 it fails to claim a device and wants to be rerun externally, after a wait
#       'err': atom, wait: atom
# 3 it fails to claim a device and wants to be rerun internally, immediately
#       'err': atom, retry: atom
# 4 it fails to claim a device and knows it can only fail
#       'err': atom, fail: atom
def claim_device(request: HttpRequest, **kwargs) -> (bool, Union[Device, ClaimFailure]):
    device_type: str = kwargs.get('device_type')
    search_list = [('type', device_type), ('enabled', True), ('allocated', False)]
    # unk_list: list = deepcopy(search_list)
    # unk_list.append(('status', '---'))
    # unk_device: Device = find_device_by_list(unk_list)
    # if unk_device is not None:
    #     TODO add async check status
    # pass

    ready_list: list = deepcopy(search_list)
    ready_list.append(('status', 'ON'))
    soon_list: list = deepcopy(search_list)
    soon_list.append(('status', 'RES'))
    # off_list: list = deepcopy(search_list)
    # off_list.append(('status', 'OFF'))

    ready_device: Device = find_device_by_list(ready_list)
    soon_device: Device = find_device_by_list(soon_list)
    # off_device: Device = find_device_by_list(off_list)

    # TODO add logic for restarting devices
    #  handle off devices
    if ready_device is None:
        # log.info(log_request(request, "No more devices available of type '%s'" % device_type))

        if soon_device is not None:
            return False, ClaimFailure.wait

        # if off_device is not None:
        # TODO add asynch turn on device and alter response
        # return HttpResponse("Retry in a few seconds", status=409)
        # return HttpResponse("No device of type '%s' unclaimed, enabled and on" % device_type, status=503)

        # no devices ready, no device restarting, no device off
        return False, ClaimFailure.fail

        # else
    try:
        with transaction.atomic():
            instance: Device = Device.objects.select_for_update(nowait=False).get(pk=ready_device.pk)
            if instance.allocated is True:
                raise RuntimeError('"allocated" Value changed since read')
            if instance.owner is not None:
                raise RuntimeError('"owner" Value changed since read')
            kv_pairs = {"allocated": True, "owner": request.META['REMOTE_ADDR']}
            for key in kv_pairs.keys():
                instance.__dict__[key] = kv_pairs.get(key)
            instance.save()
    except RuntimeError as e:
        # log.critical(" ---DEBUG--- %s" % e)
        return False, ClaimFailure.retry

    # so we successfully searched the list of devices and while we decided on one of them the one we ended up going for
    # did not end up being altered by another  ni the mean time
    # so this means success and only this thread owns it now
    return True, instance


def get(request: HttpRequest, **kwargs):
    device_type: str = kwargs.get('device_type')
    if not check_device_type_exists(device_type):
        # log.info(log_request(request, "Device type unknown: '%s'" % device_type))
        return HttpResponse("Device type '%s' unknown" % device_type, status=400)

    def make_409():
        return HttpResponse("Retry in a few seconds", status=409)

    def make_503():
        return HttpResponse("No device of type '%s' unclaimed, enabled and on" % device_type, status=503)

    def response_switch(reason: ClaimFailure):
        switch_map = {
            ClaimFailure.wait: make_409,
            ClaimFailure.retry: claim_recurse,
            ClaimFailure.fail: make_503,
        }
        # log.critical(" ---DEBUG--- comparing reason %s with %s" % (reason, ClaimFailure.fail))
        return switch_map.get(reason)()

    def claim_recurse():
        (success, elem2) = claim_device(request, **kwargs)
        if not success:
            # log.critical(" ---DEBUG--- %s %s" % (success, elem2))
            return response_switch(elem2)
        # else

        device_dict = elem2.as_dict()
        print(device_dict)
        device_ip = device_dict['ip']
        print(device_ip)
        device_port = device_dict['port']
        print(device_port)
        # log.info(log_request(request, "Device: ip '%s' port '%s' allocated to '%s'" %
        #                      (device_ip, device_port, request.META['REMOTE_ADDR'])))
        # log.critical(log_request(request, "Device: ip '%s' port '%s' allocated to '%s'" %
        #                      (device_ip, device_port, request.META['REMOTE_ADDR'])))
        return HttpResponse("%s:%s" % (device_ip, device_port))

    return claim_recurse()
