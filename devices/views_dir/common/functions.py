from devices.model_dir.DeviceTypes import DeviceType
from devices.model_dir.Devices import Device

from devices.common.functions import safe_get_model_all


def check_device_type_exists(device_type: str):
    for existing_device_type in safe_get_model_all(DeviceType):
        if str(existing_device_type) == device_type:
            return True
    return False


def find_device_by_list(value_list: list):
    ret_device = None
    sorted_device_list = list(safe_get_model_all(Device))

    def sort_prio(val):
        return val.priority
    sorted_device_list.sort(key=sort_prio)

    # log.critical(sorted_device_list)

    for device in sorted_device_list:
        for value_tuple in value_list:
            if compare_device_by_tuple(device, value_tuple):
                ret_device = device
                continue
            # else
            ret_device = None
            break
        if ret_device is not None:
            # print("will return '%s'" % ret_device)
            return ret_device
    return ret_device


def compare_device_by_tuple(device: Device, value_tuple: tuple):
    # print("comparing '%s'  and '%s'" % (device.as_dict()[value_tuple[0]], value_tuple[1]))
    if str(device.as_dict()[value_tuple[0]]) == str(value_tuple[1]):
        # print("True")
        return True
    # else
    # print("False")
    return False
