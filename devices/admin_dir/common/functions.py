from django.db.models.query_utils import DeferredAttribute
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor

from devices.model_dir.DeviceTypes import DeviceType
from devices.model_dir.DeviceFunction import DeviceFunction
from devices.common.functions import safe_get_model_all


def default_type_switch(object_type):
    switch = {
        DeferredAttribute: True,
        ForwardManyToOneDescriptor: True,
    }
    return switch.get(object_type, False)


def default_key_switch(key):
    switch = {
        'key': True,
        'id': True,
    }
    if '_id' in key:
        return True
    return switch.get(key, False)


def get_all_existing_functions_for_type(filter_type: DeviceType):
    function_list = []
    for function in safe_get_model_all(DeviceFunction):
        if not function.exists():
            continue
        if not filter_type == str(function.type_association):
            continue
        function_list.append(function)
    return function_list
