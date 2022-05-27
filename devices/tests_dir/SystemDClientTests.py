from os import path
from os import environ as os_environ
from platform import system as platform_name
from time import sleep
from unittest import skipUnless

from django.test import LiveServerTestCase, tag

from devices.model_dir.DeviceTypes import DeviceType
from devices.model_dir.Devices import Device
from devices.model_dir.DeviceFunction import DeviceFunction
from devices.common.functions import cleaned_popen_call, safe_get_model_by, safe_delete_all
from devices.tests_dir.common.functions import check_exit_code, check_stderr_for, check_stdout_for_dict, \
    check_stdout_for, check_stdout_not, check_stdout_for_any_line, make_devices, make_function
from devices.tests_dir.common.fixtures import default_devices, cla_device, dis_device, real_emu

from pathing_info import basedir

from log_config import set_log_level

log = set_log_level()
adms_run_integration: bool = False
if os_environ.get('ADMS_RUN_INTEGRATION') is not None:
    log.warning("run integration TRUE")
    adms_run_integration: bool = True


def script_call(i_command: list):  # test setup code # pra-broke-gma: no cover
    def decorator(fun):
        def wrapper(*args, **kwargs):
            cyg_script_path = path.join(basedir, 'systemd_client/cyg_script.bat')
            script_path = path.join(basedir, 'systemd_client/%s' % i_command[0])
            command = [script_path,
                       i_command[1],
                       'SERVER', '127.0.0.1',
                       'PORT', args[0].live_server_url.split(':')[2]]

            def windows():  # platform specific # pragma: no cover
                command.insert(0, cyg_script_path)

            def linux():  # platform specific # pragma: no cover
                pass

            def default():  # platform specific # pragma: no cover
                print("Warning! Unsupported Platform detected %s." % platform_name())

            def platform_switch():
                switch = {
                    'Linux': linux,
                    'Windows': windows,
                }
                return switch.get(platform_name(), default)

            # executes only the platform specific function
            platform_switch()()

            for c in i_command[2:]:
                command.append(c)
            log.debug("    dbg - script call - (%s)" % command)
            stdout, stderr, exit_code = cleaned_popen_call(command)
            log.debug("    dbg - script call - stdout - begin\n%s\n    dbg - script call - stdout - end" % stdout)
            log.debug("    dbg - script call - stderr - begin\n%s\n    dbg - script call - stderr - end" % stderr)
            log.debug("    dbg - script call - exit code - (%s)" % exit_code)
            return fun(*args, **{'stderr': stderr, 'stdout': stdout,
                                 'exit_code': exit_code, **kwargs})

        return wrapper

    return decorator


def fun_tear_down(i_command: list):  # test setup code # pra-break-gma: no cover
    def decorator(fun):
        def wrapper(*args, **kwargs):
            @script_call(i_command)
            def cleanup_call(*args, **kwargs):
                log.debug("          dbg - tear down - end")

            try:
                ret_val = fun(*args, **kwargs)
            finally:
                log.debug("          dbg - tear down - begin")
                cleanup_call(*args, **kwargs)
            return ret_val

        return wrapper

    return decorator


def _device_status_handling(condition: str, device_key: str) -> bool:
    sleep(10)
    for i in range(0, 20):
        device = safe_get_model_by(Device, pk=device_key)
        log.debug("    dbg - device status - is (%s) - expected (%s)" % (device.status, condition))
        if device.status == condition:
            return True
        if device.status != condition:  # hopefully unused # pragma: no cover
            log.debug("    sleeping 20")
            sleep(20)
    return False


def fun_pre_condition_device_status_delay(condition: str, device_key: str):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            if _device_status_handling(condition, device_key):
                return fun(*args, **kwargs)
            else:
                args[0].fail("Device did not enter expected state during test")  # hopefully unused  pragma: no cover

        return wrapper

    return decorator


def fun_post_condition_device_status_delay(condition: str, device_key: str):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            ret_val = None
            try:
                ret_val = fun(*args, **kwargs)
            finally:
                if _device_status_handling(condition, device_key):
                    return ret_val
                else:
                    args[0].fail(
                        "Device did not enter expected state during test")  # hopefully unused  pragma: no cover

        return wrapper

    return decorator


def fun_set_up(i_command: list):  # test setup code # pra-break-gma: no cover
    def decorator(fun):
        def wrapper(*args, **kwargs):
            @script_call(i_command)
            def setup_call(*args, **kwargs):
                log.debug("          dbg - set up - end")

            log.debug("          dbg - set up - begin")
            setup_call(*args, **kwargs)
            return fun(*args, **kwargs)

        return wrapper

    return decorator


def real_emu(i: int = 1):
    def switcher(amount: int):
        mapper = {
            1: {'0': {'type': 'cloud-default', 'ip': '10.21.2.11', 'port': 5559}},
            2: {'0': {'type': 'cloud-default', 'ip': '10.21.2.11', 'port': 5559},
                '1': {'type': 'cloud-default', 'ip': '10.21.2.11', 'port': 5561}},
        }
        return mapper.get(amount)

    return default_devices(i, **(switcher(i)))


def ip_port(func: callable, index: int = 0):
    return ['ip', "%s" % func(index + 1)[index]['ip'],
            'port', "%s" % func(index + 1)[index]['port']]


class SystemDClientTests(LiveServerTestCase):
    log = set_log_level()

    def tearDown(self):
        safe_delete_all(DeviceFunction)
        safe_delete_all(Device)
        safe_delete_all(DeviceType)

    # devices.sh

    @script_call(['devices.sh', 'get'])
    def test_client_devices_get_pos(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for_dict(self, {}, 0, **kwargs)

    @script_call(['devices.sh', ''])
    def test_client_devices_http_verb_missing(self, **kwargs):
        check_exit_code(self, 40, **kwargs)
        check_stderr_for(self, "Unknown request type ''", **kwargs)

    @script_call(['devices.sh', 'BAD-ARG'])
    def test_client_devices_http_verb_bad(self, **kwargs):
        check_exit_code(self, 40, **kwargs)
        check_stderr_for(self, "Unknown request type 'BAD-ARG'", **kwargs)

    @script_call(['devices.sh', 'put'])
    def test_client_devices_put(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "405 Method Not Allowed", **kwargs)

    # claimdevice.sh

    @make_devices(default_devices())
    @script_call(['claimdevice.sh', 'get', 'type', "%s" % default_devices()[0]['type']])
    def test_client_claim_get_pos(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "%s:%s" % (default_devices()[0]['ip'], default_devices()[0]['port']), **kwargs)

    @make_devices(default_devices())
    @script_call(['claimdevice.sh', 'get', 'type', "%s" % default_devices()[0]['type'],
                  'timeout', '10',
                  'alloc', 'ignored', 'desc', 'ignored', 'ip', 'ignored', 'port', 'ignored', 'owner', 'ignored',
                  'value', 'ignored', 'ignored', 'func', 'ignored', 'adb', 'ignored', 'devfile', 'ignored',
                  'fileprefix', 'ignored'])
    def test_client_claim_get_pos_all_params(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "%s:%s" % (default_devices()[0]['ip'], default_devices()[0]['port']), **kwargs)

    @script_call(['claimdevice.sh', ''])
    def test_client_claim_http_verb_missing(self, **kwargs):
        check_exit_code(self, 40, **kwargs)
        check_stderr_for(self, "Unknown request type ''", **kwargs)

    @script_call(['claimdevice.sh', 'BAD-ARG'])
    def test_client_claim_http_verb_bad(self, **kwargs):
        check_exit_code(self, 40, **kwargs)
        check_stderr_for(self, "Unknown request type 'BAD-ARG'", **kwargs)

    @script_call(['claimdevice.sh', 'get'])
    def test_client_claim_get_neg_missing_type(self, **kwargs):
        check_exit_code(self, 80, **kwargs)
        check_stderr_for(self, "Type argument must be given", **kwargs)

    @script_call(['claimdevice.sh', 'get', 'type'])
    def test_client_claim_get_neg_missing_type_arg(self, **kwargs):
        check_exit_code(self, 80, **kwargs)
        check_stderr_for(self, "Type argument must be given", **kwargs)

    @script_call(['claimdevice.sh', 'get', 'type', 'DNE'])
    def test_client_claim_get_neg_type_DNE(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "400 Bad Request", **kwargs)
        check_stdout_for(self, "Device type 'DNE' unknown", **kwargs)

    @script_call(['claimdevice.sh', 'get', 'also'])
    def test_client_claim_get_neg_param_unknown(self, **kwargs):
        check_exit_code(self, 30, **kwargs)
        check_stderr_for(self, "Unknown option 'also'", **kwargs)

    @script_call(['claimdevice.sh', 'put', 'type', 'ignored'])
    def test_client_claim_put(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "405 Method Not Allowed", **kwargs)

    # releasedevice.sh

    @make_devices(cla_device())
    @script_call(['releasedevice.sh', 'get', 'alloc', 'ignored', 'desc', 'ignored', 'owner', 'ignored', 'value',
                  'ignored', 'ignored', 'func', 'ignored', 'adb', 'ignored', 'devfile', 'ignored', 'fileprefix',
                  'ignored', 'type', 'ignored', 'timeout', '10', ] + ip_port(cla_device))
    def test_client_release_get_pos_all_params(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        expected: dict = cla_device()[0]
        expected.update(**{'owner': None, 'allocated': False})
        check_stdout_for_dict(self, expected, **kwargs)

    @make_devices(cla_device())
    @script_call(['releasedevice.sh', 'get'] + ip_port(cla_device))
    def test_client_release_get_pos(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        expected: dict = cla_device()[0]
        expected.update(**{'owner': None, 'allocated': False})
        check_stdout_for_dict(self, expected, **kwargs)

    @script_call(['releasedevice.sh', ''])
    def test_client_release_http_verb_missing(self, **kwargs):
        check_exit_code(self, 40, **kwargs)
        check_stderr_for(self, "Unknown request type ''", **kwargs)

    @script_call(['releasedevice.sh', 'BAD-ARG'])
    def test_client_release_http_verb_bad(self, **kwargs):
        check_exit_code(self, 40, **kwargs)
        check_stderr_for(self, "Unknown request type 'BAD-ARG'", **kwargs)

    @script_call(['releasedevice.sh', 'put', 'ip', 'ignored', 'port', 'ignored'])
    def test_client_release_put(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "405 Method Not Allowed", **kwargs)

    @script_call(['releasedevice.sh', 'get', 'port', 'ignored'])
    def test_client_release_get_neg_missing_ip(self, **kwargs):
        check_exit_code(self, 60, **kwargs)
        check_stderr_for(self, "Ip argument must be given", **kwargs)

    @script_call(['releasedevice.sh', 'get', 'port', 'ignored', 'ip'])
    def test_client_release_get_neg_missing_ip_arg(self, **kwargs):
        check_exit_code(self, 60, **kwargs)
        check_stderr_for(self, "Ip argument must be given", **kwargs)

    @script_call(['releasedevice.sh', 'get'])
    def test_client_release_get_neg_missing_all(self, **kwargs):
        check_exit_code(self, 60, **kwargs)
        check_stderr_for(self, "Ip argument must be given", **kwargs)

    @script_call(['releasedevice.sh', 'get', 'port', 'DNE', 'ip', 'DNE'])
    def test_client_release_get_neg_device_dne(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "404 Not Found", **kwargs)
        check_stdout_for_dict(self, {'Error': "Device 'DNE-DNE' does not exist"}, **kwargs)

    # android-device-claim.sh

    @script_call(['android-device-claim.sh', '', 'devfile', 'test_device_config'])
    def test_client_adc_neg_missing_verb(self, **kwargs):
        check_exit_code(self, 10, **kwargs)
        check_stderr_for(self, "claim||release||reclaim command must be given", **kwargs)
        check_stdout_not(self, "connected to ", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    @script_call(['android-device-claim.sh', 'claim', 'type', 'DNE', 'devfile', 'test_device_config'])
    def test_client_adc_claim_neg_type_dne(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "400 Bad Request", **kwargs)
        check_stdout_for(self, "Device type 'DNE' unknown", **kwargs)
        check_stdout_not(self, "connected to ", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    @make_devices(cla_device())
    @script_call(['android-device-claim.sh', 'claim', 'type', "%s" % cla_device()[0]['type'],
                  'devfile', 'test_device_config'])
    def test_client_adc_claim_neg_all_claimed(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "503 Service Unavailable", **kwargs)
        check_stdout_for(self, "No device of type '%s' unclaimed, enabled and on" % cla_device()[0]['type'], **kwargs)
        check_stdout_not(self, "connected to ", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    @make_devices(dis_device())
    @script_call(['android-device-claim.sh', 'claim', 'type', "%s" % dis_device()[0]['type'],
                  'devfile', 'test_device_config'])
    def test_client_adc_claim_neg_not_enabled(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "503 Service Unavailable", **kwargs)
        check_stdout_for(self, "No device of type '%s' unclaimed, enabled and on" % dis_device()[0]['type'], **kwargs)
        check_stdout_not(self, "connected to ", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    @script_call(['android-device-claim.sh', 'release', 'devfile', 'a_name'])
    def test_client_adc_release_neg_no_dev_file(self, **kwargs):
        check_exit_code(self, 11, **kwargs)
        check_stderr_for(self, "No config file found '/tmp/get_android_device/a_name'", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    # TODO:
    # make setup functions/decorators to create arbitrary devfiles
    # use this to create tests for the 'adc release' calls which are in various states of bad configurations
    # make sure that the output is such that it can be inferred what the nature of the bad configuration is

    @script_call(['android-device-claim.sh', 'reclaim', 'devfile', 'test_devfile'])
    def test_client_adc_reclaim_neg_no_dev_file(self, **kwargs):
        check_exit_code(self, 11, **kwargs)
        check_stderr_for(self, "No config file found '/tmp/get_android_device/test_devfile'", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    # TODO:
    # as above for release

    @script_call(['android-device-claim.sh', 'release-all', 'fileprefix', 'test_prefix'])
    def test_client_adc_release_all_no_devfiles(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stdout_for(self, "No devices-files for fileprefix test_prefix found!", **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    # functions

    @make_devices(default_devices())
    @make_function("check_params", "%s" % default_devices()[0]['type'])
    @script_call(['function.sh', 'get', 'func', 'check_params'] + ip_port(default_devices))
    def test_client_function_get_pos(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)

    @make_devices(default_devices())
    @script_call(['function.sh', 'get', 'func', 'DNE'] + ip_port(default_devices))
    def test_client_function_get_neg_fun_dne_in_db(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        expected: dict = {'Error': "DeviceFunction 'DNE' does not exist in database"}
        check_stdout_for_dict(self, expected, **kwargs)

    @make_devices(default_devices())
    @make_function('DNE', default_devices()[0]['type'])
    @script_call(['function.sh', 'get', 'func', 'DNE'] + ip_port(default_devices))
    def test_client_function_get_neg_fun_dne_as_script(self, **kwargs):
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        expected: dict = {'WARN': "DeviceFunction 'DNE' does not exist as a script (but does in database)"}
        check_stdout_for_dict(self, expected, **kwargs)

    @script_call(['function.sh', 'get', 'ip', 'DNE', 'port', 'DNE', 'func', 'ignored'])
    def test_client_function_get_neg_device_dne(self, **kwargs):
        check_exit_code(self, 72, **kwargs)
        check_stderr_for(self, "404 Not Found", **kwargs)
        expected: dict = {'Error': "Device 'DNE-DNE' does not exist"}
        check_stdout_for_dict(self, expected, **kwargs)

    # skip tests go here

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @script_call(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type']])
    @fun_tear_down(['android-device-claim.sh', 'release'])
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_adc_claim_pos(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_claim_pos')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for_any_line(self, "connected to %s" % real_emu()[0]['ip'], **kwargs)
        check_stdout_not(self, "disconnected %s" % real_emu()[0]['ip'], **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @script_call(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type'],
                  'timeout', '10', 'devfile', 'test_devfile',
                  'alloc', 'ignored', 'desc', 'ignored', 'owner', 'ignored', 'value', 'ignored', 'ignored',
                  'func', 'ignored', 'adb', 'ignored', 'fileprefix', 'ignored', 'ip', 'ignored', 'port', 'ignored'])
    @fun_tear_down(['android-device-claim.sh', 'release', 'devfile', 'test_devfile'])
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_adc_claim_pos_all_params(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_claim_pos_all_params')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "connected to %s" % real_emu()[0]['ip'], **kwargs)
        check_stdout_not(self, "disconnected ", **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type']])
    @script_call(['android-device-claim.sh', 'release'])
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_adc_release_pos(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_release_pos')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "disconnected %s" % real_emu()[0]['ip'], **kwargs)
        check_stdout_for_dict(self, real_emu()[0], 1, **kwargs)
        check_stdout_not(self, "connected to %s" % real_emu()[0]['ip'], **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type'], 'devfile', 'test_devfile'])
    @script_call(['android-device-claim.sh', 'release',
                  'timeout', '10', 'devfile', 'test_devfile',
                  'alloc', 'ignored', 'desc', 'ignored', 'owner', 'ignored', 'value', 'ignored', 'ignored',
                  'func', 'ignored', 'adb', 'ignored', 'fileprefix', 'ignored', 'ip', 'ignored', 'port', 'ignored'])
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_adc_release_pos_all_params(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_release_pos_all_params')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "disconnected %s" % real_emu()[0]['ip'], **kwargs)
        check_stdout_for_dict(self, real_emu()[0], 1, **kwargs)
        check_stdout_not(self, "connected to %s" % real_emu()[0]['ip'], **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type']])
    @script_call(['android-device-claim.sh', 'reclaim', 'type', real_emu()[0]['type']])
    @fun_tear_down(['android-device-claim.sh', 'release'])
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_adc_reclaim_pos(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_reclaim_pos')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "disconnected %s" % real_emu()[0]['ip'], **kwargs)
        check_stdout_for_dict(self, real_emu()[0], 1, **kwargs)
        check_stdout_for(self, "connected to %s" % real_emu()[0]['ip'], 2, **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type'], 'devfile', 'test_devfile'])
    @script_call(['android-device-claim.sh', 'reclaim', 'type', real_emu()[0]['type'],
                  'timeout', '10', 'devfile', 'test_devfile',
                  'alloc', 'ignored', 'desc', 'ignored', 'owner', 'ignored', 'value', 'ignored', 'ignored',
                  'func', 'ignored', 'adb', 'ignored', 'fileprefix', 'ignored', 'ip', 'ignored', 'port', 'ignored'])
    @fun_tear_down(['android-device-claim.sh', 'release', 'devfile', 'test_devfile'])
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_adc_reclaim_pos_all_params(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_reclaim_pos_all_params')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "disconnected %s" % real_emu()[0]['ip'], **kwargs)
        check_stdout_for_dict(self, real_emu()[0], 1, **kwargs)
        check_stdout_for(self, "connected to %s" % real_emu()[0]['ip'], 2, **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu(2))
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu, 1))
    @fun_pre_condition_device_status_delay('ON', real_emu(2)[0]['key'])
    @fun_pre_condition_device_status_delay('ON', real_emu(2)[1]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu(2)[0]['type'], 'devfile', 'test_prefix-0'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu(2)[1]['type'], 'devfile', 'test_prefix-1'])
    @script_call(['android-device-claim.sh', 'release-all', 'fileprefix', 'test_prefix'])
    @fun_post_condition_device_status_delay('ON', real_emu(2)[0]['key'])
    @fun_post_condition_device_status_delay('ON', real_emu(2)[1]['key'])
    def test_client_adc_release_all_pos(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_release_all_pos')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for(self, "disconnected %s:%s" % (real_emu(2)[0]['ip'], real_emu(2)[0]['port']), **kwargs)
        check_stdout_for(self, "disconnected %s:%s" % (real_emu(2)[1]['ip'], real_emu(2)[1]['port']), 2, **kwargs)
        check_stdout_for_dict(self, real_emu(2)[0], 1, **kwargs)
        check_stdout_for_dict(self, real_emu(2)[1], 3, **kwargs)
        check_stdout_not(self, "connected to %s:%s" % (real_emu(2)[0]['ip'], real_emu(2)[0]['port']), **kwargs)
        check_stdout_not(self, "connected to %s:%s" % (real_emu(2)[1]['ip'], real_emu(2)[1]['port']), **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu(2))
    @make_function('start', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu, 1))
    @fun_pre_condition_device_status_delay('ON', real_emu(2)[0]['key'])
    @fun_pre_condition_device_status_delay('ON', real_emu(2)[1]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu(2)[0]['type'], 'devfile', 'test_prefix-0'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu(2)[1]['type'], 'devfile', 'test_prefix-1'])
    @script_call(['android-device-claim.sh', 'release-all', 'fileprefix', 'test_prefix',
                  'timeout', '10', 'devfile', 'ignored',
                  'alloc', 'ignored', 'desc', 'ignored', 'owner', 'ignored', 'value', 'ignored', 'ignored',
                  'func', 'ignored', 'adb', 'ignored', 'ip', 'ignored', 'port', 'ignored', 'type', 'ignored'])
    @fun_post_condition_device_status_delay('ON', real_emu(2)[0]['key'])
    @fun_post_condition_device_status_delay('ON', real_emu(2)[1]['key'])
    def test_client_adc_release_all_pos_all_params(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_adc_release_all_pos_all_params')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        check_stdout_for_any_line(self, "disconnected %s:%s" % (real_emu(2)[0]['ip'], real_emu(2)[0]['port']), **kwargs)
        check_stdout_for_any_line(self, "disconnected %s:%s" % (real_emu(2)[1]['ip'], real_emu(2)[1]['port']), **kwargs)
        check_stdout_for_dict(self, real_emu(2)[0], 1, **kwargs)
        check_stdout_for_dict(self, real_emu(2)[1], 3, **kwargs)
        check_stdout_not(self, "connected to %s:%s" % (real_emu(2)[0]['ip'], real_emu(2)[0]['port']), **kwargs)
        check_stdout_not(self, "connected to %s:%s" % (real_emu(2)[1]['ip'], real_emu(2)[1]['port']), **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    # this has an ugly dependency to the existence of the correct type of function script
    @make_function("start", real_emu()[0]['type'])
    @make_function("check_status", real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @script_call(['function.sh', 'get', 'func', 'check_status'] + ip_port(real_emu))
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_function_get_pos_real_emu_check(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_function_get_pos_real_emu_check')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    # this has an ugly dependency to the existence of the correct type of function script
    @make_function("start", real_emu()[0]['type'])
    @make_function("restart", real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @script_call(['function.sh', 'get', 'func', 'restart'] + ip_port(real_emu))
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_function_get_pos_real_emu_restart(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_function_get_pos_real_emu_restart')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        sleep(40)
        for i in range(0, 15, 1):
            device: Device = safe_get_model_by(Device, pk=real_emu()[0]['key'])
            if str(device.status) == "ON":
                return
            sleep(3)
        self.fail("device did not start within 85 seconds"
                  "\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                  (kwargs.get('stderr'), kwargs.get('stdout')))

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function("stop", real_emu()[0]['type'])
    @make_function("start", real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @script_call(['function.sh', 'get', 'func', 'stop'] + ip_port(real_emu))
    @fun_post_condition_device_status_delay('OFF', real_emu()[0]['key'])
    # @fun_tear_down(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    # @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_function_get_pos_real_emu_stop(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_function_get_pos_real_emu_stop')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        sleep(10)
        for i in range(0, 15, 1):
            device: Device = safe_get_model_by(Device, pk=real_emu()[0]['key'])
            if str(device.status) == "ON":
                return
            sleep(2)
        self.fail("device did not stop within 40sec"
                  "\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                  (kwargs.get('stderr'), kwargs.get('stdout')))

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function("stop", real_emu()[0]['type'])
    @make_function("start", real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'stop'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('OFF', real_emu()[0]['key'])
    @script_call(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_post_condition_device_status_delay('ON', real_emu()[0]['key'])
    def test_client_function_get_pos_real_emu_start(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_function_get_pos_real_emu_start')
        check_exit_code(self, 0, **kwargs)
        check_stderr_for(self, "200 OK", **kwargs)
        sleep(60)
        for i in range(0, 30, 1):
            device: Device = safe_get_model_by(Device, pk=real_emu()[0]['key'])
            if str(device.status) == "ON":
                return
            sleep(4)
        self.fail("device did not start within 3 min"
                  "\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                  (kwargs.get('stderr'), kwargs.get('stdout')))

    @tag('non-parallel')
    @skipUnless(adms_run_integration, "uses active emulators, integration test")
    @make_devices(real_emu())
    @make_function('start', real_emu()[0]['type'])
    @make_function('stop', real_emu()[0]['type'])
    @fun_set_up(['function.sh', 'get', 'func', 'start'] + ip_port(real_emu))
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @fun_set_up(['android-device-claim.sh', 'claim', 'type', real_emu()[0]['type']])
    @fun_pre_condition_device_status_delay('ON', real_emu()[0]['key'])
    @script_call(['android-device-claim.sh', 'restart'] + ip_port(real_emu))
    def test_client_function_get_pos_connected_emu_restart(self, **kwargs):  # skip # pra-break-gma: no cover
        log.debug('    dbg - test checks - test_client_function_get_pos_connected_emu_restart')
        log.debug("HERE IS WHAT WE GOT -------------------------------------"
                  "\n  ---  STDERR  ---\n%s\n  ---  STDOUT  ---\n%s" %  # pragma: no cover
                  (kwargs.get('stderr'), kwargs.get('stdout')))
        check_exit_code(self, 0, **kwargs)
        check_stdout_for_any_line(self, "stop DONE", **kwargs)
        check_stdout_for_any_line(self, "start DONE", **kwargs)
        check_stdout_for_any_line(self, "restart DONE", **kwargs)
