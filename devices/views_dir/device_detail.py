import logging

from django.http import HttpRequest, JsonResponse

from devices.model_dir.Devices import Device
from devices.views_dir.common.logging import log_request
from devices.common.functions import safe_get_model_by

log = logging.getLogger('adms.views')


def get(request: HttpRequest, **kwargs):
    log.info(log_request(request, ""))
    device_key = kwargs.get('device_key')
    # device_key = "%s-%s" % (kwargs.get('device_ip'), kwargs.get('device_port'))
    try:
        device = safe_get_model_by(Device, pk=device_key)
    except Device.DoesNotExist:
        # TODO extract function and make all that return this use it
        return JsonResponse({'Error': "Device '%s' does not exist" % device_key}, status=404)
    return JsonResponse(device.as_dict())
