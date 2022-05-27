# from cache_memoize import cache_memoize


def real_emu(i: int = 1):
    def switcher(amount: int):
        mapper = {
            1: {'0': {'type': 'cloud-default', 'ip': '10.21.2.11', 'port': 5559}},
            2: {'0': {'type': 'cloud-default', 'ip': '10.21.2.11', 'port': 5559},
                '1': {'type': 'cloud-default', 'ip': '10.21.2.11', 'port': 5561}},
        }
        return mapper.get(amount)

    return default_devices(i, **(switcher(i)))


# this actually makes it slower, not expensive enough and/or enough calls,  yet
# @cache_memoize(60)
def default_devices(amount: int = 1, **changes):
    def dns_gen(index: int) -> str:
        return "1.1.1.%s" % index

    def port_gen(index: int) -> int:
        return index + 1110

    device_list: list = []
    for i in range(amount):
        device_list.append({'ip': dns_gen(i), 'port': port_gen(i), 'type': 'type-0', 'description': "desc-0",
                            'status': "ON", 'enabled': True, 'allocated': False, 'owner': None, 'priority': 9999})
    for key in changes.keys():
        device_list[int(key)].update(**changes[key])
    for device in device_list:
        device.update(**{'key': "%s-%s" % (device['ip'], device['port'])})

    return device_list


def res_device(*args):
    return default_devices(**{'0': {'status': 'RES'}})


def off_device(*args):
    return default_devices(**{'0': {'status': 'OFF'}})


def res_fail_fun_device(*args):
    return default_devices(**{'0': {'type': 'type-fail', 'owner': '127.0.0.1', 'allocated': False}})


def cla_device(*args):
    return default_devices(**{'0': {'owner': '127.0.0.1', 'allocated': True}})


def dis_device(*args):
    return default_devices(**{'0': {'enabled': False}})
