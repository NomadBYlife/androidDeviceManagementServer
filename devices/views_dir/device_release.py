from django.http import HttpRequest, JsonResponse

from devices.model_dir.Devices import Device
from devices.model_dir.DeviceFunction import DeviceFunction
from devices.views_dir.common.logging import log_request
from devices.common.functions import safe_get_model_by, safe_set_model_values

import logging
log = logging.getLogger('adms.views')


def get(request: HttpRequest, **kwargs):
    log.info(log_request(request, ""))
    device_key = kwargs.get('device_key')
    try:
        device: Device = safe_get_model_by(Device, pk=device_key)
    except Device.DoesNotExist:
        # TODO extract function and make all endpoints that return this use it
        log.warning(log_request(request, "Failed to find device: '%s'" % device_key))
        return JsonResponse({'Error': "Device '%s' does not exist" % device_key}, status=404)

    request_host_ip = request.META['REMOTE_ADDR']
    if device.owner != request_host_ip:
        log.warning(log_request(request, "Device being released by a host which is not the owner!\n  "
                                         "Owner was: '%s'  Released by: '%s'" % (device.owner, request_host_ip)))

    safe_set_model_values(Device, device_key, allocated=False, owner=None)
    log.info(log_request(request, "Released device: '%s'" % device_key))
    # TODO restarting the device should go here
    try:
        restart_device: DeviceFunction = safe_get_model_by(DeviceFunction, key="%s-%s" % (device.type, 'restart'))
        if restart_device.exists():
            tpe = kwargs.get('the_tpe')
            tpe.submit(restart_device.execute_function, device_key)
            # restart_device.execute_function(device)
            # if int(restart_device.exit_code) != 0 and int(restart_device.exit_code) != 2:
            #    log.warning("Device Function with unexpected exit code:\n\t%s\n\t%s\n\t%s" %
            #                (restart_device.stdout, restart_device.stderr, restart_device.exit_code))
    except DeviceFunction.DoesNotExist:
        # TODO add log output because somebody needs to know that what they are calling doesnt exist
        log.warning("Function '%s-%s' was called but does not exist" % (device.type, 'restart'))
    return JsonResponse(safe_get_model_by(Device, pk=device_key).as_dict())
