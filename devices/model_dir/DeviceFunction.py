import os
import threading
from copy import deepcopy
from collections import OrderedDict
from platform import system as platform_system

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from devices.model_dir.Devices import Device
from devices.model_dir.common.help_texts import device_function_association_type, device_function_name_help
from devices.common.functions import safe_get_model_all, safe_get_model_by, safe_delete_instance, \
    safe_set_model_values
from devices.common.functions import unsafe_create

from pathing_info import basedir
from devices.common.functions import cleaned_popen_call

from log_config import set_log_level

log = set_log_level()
function_dir = os.path.join(basedir, 'devices', 'function_dir')


class DeviceFunction(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = self.get_type_name_slug()
        self.check_exist()

    def __str__(self):
        return str(self.as_dict())

    def as_dict(self):
        # noinspection PyTypeChecker
        order_dict: OrderedDict = \
            {'type_association': '1', 'function_name': '1', 'script_found': '1'}
        order_dict.update(deepcopy(vars(self)))
        if '_state' in order_dict.keys():
            order_dict.pop('_state')
        if 'type_association_id' in order_dict.keys():
            order_dict.update({'type_association': order_dict['type_association_id']})
            order_dict.pop('type_association_id')
        norm_dict: dict = dict(order_dict)
        return norm_dict

    def get_type_name_slug(self):
        fun_dict: dict = vars(self)
        device_type = str(fun_dict['type_association_id'])
        fun_name: str = str(fun_dict['function_name'])
        current_key: str = "%s-%s" % (device_type, fun_name)
        return current_key

    def check_exist(self):
        self.script_path = os.path.join(function_dir, str(self.type_association), "%s.sh" % str(self.function_name))

        if os.path.exists(str(self.script_path)):
            # logger.critical("path exists")
            self.script_found = True
        else:
            # logger.critical("DOES NOT exist!")
            self.script_found = False

    def exists(self):
        self.check_exist()
        return self.script_found

    def validate_type_name_unique(self):
        self_type_name = self.get_type_name_slug()
        error = ValidationError(_('Combination of type and name: %(type_name)s is not unique'),
                                params={'type_name': self_type_name})

        type_name_list: list = []
        for fun in safe_get_model_all(DeviceFunction):
            if fun.key == self.key:
                pass
            else:
                type_name: str = fun.get_type_name_slug()
                type_name_list.append(type_name)
        if self_type_name in type_name_list:
            raise error

    # this function shall only be called from within a transaction and uses unsafe calls
    def fix_deleted_type(self, sender, **kwargs):
        self.type_association = None
        self.clean()
        altered_dict = deepcopy(self.as_dict())
        altered_dict.update({'type_association': kwargs.get('device_type')})
        unsafe_create(DeviceFunction, **altered_dict)

    # this function shall only be called from within a transaction and uses unsafe calls
    def fix_changed_type(self, sender, **kwargs):
        self.type_association = kwargs.get('instance')
        self.clean()
        altered_dict = deepcopy(self.as_dict())
        altered_dict.update({'type_association': kwargs.get('device_type')})
        unsafe_create(DeviceFunction, **altered_dict)

    def key_swap(self):
        old_pk = self.pk
        self.key = self.get_type_name_slug()
        try:
            old: DeviceFunction = safe_get_model_by(DeviceFunction, pk=old_pk)
        except DeviceFunction.DoesNotExist:
            old = None
        finally:
            if old:
                safe_delete_instance(DeviceFunction, old_pk)

    def clean(self):
        super(DeviceFunction, self).clean()
        self.validate_type_name_unique()
        self.key_swap()

    def execute_function(self, device_pk):
        local_script_path = deepcopy(str(self.script_path))
        if platform_system() == 'Windows':  #   platform specific # pragma: no cover
            local_script_path = local_script_path.replace("\\", "/")
        command = [local_script_path]
        if platform_system() == 'Windows':  # platform specific # pragma: no cover
            from pathing_info import basedir
            cyg_script = os.path.join(basedir, 'cyg_script.bat')
            command.insert(0, cyg_script)
        device_dict = safe_get_model_by(Device, pk=device_pk).as_dict()
        for key in device_dict.keys():
            command.append(key)
            command.append(str(device_dict[key]))

        self.stdout = None
        self.stderr = None
        self.exit_code = None

        def exit_code_switch():
            switch = {
                0: 'ON',
                2: 'OFF',
                3: 'LOC',
            }
            return switch.get(self.exit_code, '---')

        def default_handling():
            self.stdout, self.stderr, self.exit_code = cleaned_popen_call(command)
            safe_set_model_values(Device, device_pk, status=exit_code_switch())

        def restart_handling():
            log.debug("          dbg - re/start - run by - pid %s - tid %s" %
                      (os.getpid(), threading.current_thread().ident))
            safe_set_model_values(Device, device_pk, status='RES')
            self.stdout, self.stderr, self.exit_code = cleaned_popen_call(command)
            safe_set_model_values(Device, device_pk, status=exit_code_switch())

        def function_handling_switch():
            switch = {
                'restart': restart_handling,
                'start': restart_handling,
            }
            return switch.get(str(self.function_name), default_handling)

        function_handling_switch()()

    # slug: letters numbers underscores and hyphens
    # no whitespace or path characters ... perfect!
    function_name = models.SlugField("device_function_name", max_length=30, help_text=device_function_name_help)
    script_path = models.SlugField("script_path", max_length=300, editable=False, blank=True, default=None, null=True)
    type_association = models.ForeignKey('DeviceType', models.SET_NULL, blank=True, null=True,
                                         to_field='type_def', help_text=device_function_association_type)
    script_found = models.BooleanField('script_found', editable=False, default=False)
    key = models.CharField('PrimaryKey', db_column='key', primary_key=True, max_length=300,
                           default="%s-%s" % (str(type_association), str(function_name)), editable=False, unique=True)

    objects = None
