from django.http import HttpRequest, JsonResponse

from devices.model_dir.Devices import Device
from devices.model_dir.DeviceFunction import DeviceFunction
from devices.views_dir.common.logging import log_request
from devices.common.functions import safe_get_model_by

import logging

log = logging.getLogger('adms.views')


def get(request: HttpRequest, **kwargs):
    log.info(log_request(request, ""))
    device_key = kwargs.get('device_key')

    # noinspection PyUnresolvedReferences
    try:
        device: Device = safe_get_model_by(Device, pk=device_key)
    except Device.DoesNotExist:
        # TODO extract function and make all endpoints that return this use it
        log.debug("    dbg - device DNE - (%s)" % device_key)
        return JsonResponse({'Error': "Device '%s' does not exist" % device_key}, status=404)

    function_name = kwargs.get('function_name')
    try:
        function: DeviceFunction = safe_get_model_by(DeviceFunction, type_association=device.type,
        # function = DeviceFunction.objects.get(type_association=device.type,
                                                     function_name=function_name)
    except DeviceFunction.DoesNotExist:
        # TODO should a failure to find a function result in a non-zero non-200 response?
        log.debug("    dbg - device function DNE in DB - (%s)" % function_name)
        return JsonResponse({'Error': "DeviceFunction '%s' does not exist in database" % function_name}, status=200)

    # function.execute_function(device)
    dict_response = {}
    if function.exists():
        tpe = kwargs.get('the_tpe')
        function.execute_function(device.pk)
        tpe.submit(function.execute_function, device.pk)
        # function.execute_function(device.pk)
    else:
        dict_response = {'WARN': "DeviceFunction '%s' does not exist as a script (but does in database)" %
                                 function_name}
        log.debug("    dbg - device function DNE as script (but does in DB) - (%s)" % function_name)
    return JsonResponse(dict_response, status=200)
