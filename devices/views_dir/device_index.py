from django.http import HttpRequest, JsonResponse

from devices.model_dir.Devices import Device
from devices.common.functions import get_dict_from_model
from devices.views_dir.common.logging import log_request

from log_config import set_log_level

log = set_log_level()


def get(request: HttpRequest):
    log.info(log_request(request, ""))
    device_list = get_dict_from_model(Device)
    return JsonResponse(device_list)
