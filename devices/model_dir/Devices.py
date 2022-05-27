from copy import deepcopy
from collections import OrderedDict

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from devices.model_dir.common.validators import validate_port_range
from devices.model_dir.common.help_texts import device_type_help, device_description_help, device_status_help, \
    device_enabled_help, device_owner_help, device_allocated_help, allocation_priority_help
from devices.common.functions import safe_get_model_all, safe_get_model_by, safe_delete_instance
from devices.common.functions import unsafe_create

from log_config import set_log_level

log = set_log_level()

DEVICE_STATI = (
    ('---', 'Unknown'),
    ('ON', 'On'),
    ('OFF', 'Off'),
    ('RES', 'Restarting'),
    ('LOC', 'Locked'),
)


class Device(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = self.get_ip_port_slug()

    def __str__(self):
        return str(self.as_dict())

    def as_dict(self):
        # noinspection PyTypeChecker
        order_dict: OrderedDict = \
            {'ip': '1', 'port': '1', 'type': '1', 'description': '1', 'status': '1', 'enabled': '1',
             'allocated': '1'}
        order_dict.update(deepcopy(vars(self)))
        if '_state' in order_dict.keys():
            order_dict.pop('_state')
        # if 'id' in order_dict.keys():
        #     order_dict.pop('id')
        if 'type_id' in order_dict.keys():
            _type = order_dict['type_id']
            order_dict.pop('type_id')
            order_dict.update({'type': '%s' % _type})
        norm_dict: dict = dict(order_dict)
        # log.critical(norm_dict)
        return norm_dict

    def get_ip_port(self):
        device_dict: dict = self.as_dict()
        device_ip: str = device_dict['ip']
        device_port: str = str(device_dict['port'])
        return "%s:%s" % (device_ip, device_port)

    def get_ip_port_slug(self):
        device_dict: dict = self.as_dict()
        device_ip: str = device_dict['ip']
        device_port: str = str(device_dict['port'])
        return "%s-%s" % (device_ip, device_port)

    def validate_ip_port_unique(self):
        self_ip_port = self.get_ip_port()
        error = ValidationError(_('Combination of ip and port: %(ip_port)s is not unique'),
                                params={'ip_port': self_ip_port})

        ip_port_list: list = []
        for device in safe_get_model_all(Device):
            if device.key == self.key:
                pass
            else:
                ip_port: str = device.get_ip_port()
                ip_port_list.append(ip_port)
        if self_ip_port in ip_port_list:
            raise error

    # this function shall only be called from within a transaction and uses unsafe calls
    def fix_on_change(self, sender, **kwargs):
        self.type = kwargs.get('instance')
        self.clean()
        altered_dict = deepcopy(self.as_dict())
        altered_dict.update({'type': self.type})
        unsafe_create(Device, **altered_dict)

    def clean(self):
        super(Device, self).clean()
        self.validate_ip_port_unique()
        old_key = self.key
        self.key = self.get_ip_port_slug()
        old = None
        try:
            old: Device = safe_get_model_by(Device, pk=old_key)
        except Device.DoesNotExist:
            old = None
        finally:
            if old:
                safe_delete_instance(Device, old_key)

    ip = models.GenericIPAddressField("device_ip")
    port = models.IntegerField("device_port", validators=[validate_port_range])
    type = models.ForeignKey('DeviceType', on_delete=models.SET_NULL, blank=True, null=True, to_field='type_def',
                             help_text=device_type_help)
    description = models.SlugField("device_description", max_length=200, help_text=device_description_help)
    status = models.SlugField("device_status", max_length=20, choices=DEVICE_STATI, default='---',
                              help_text=device_status_help)
    enabled = models.BooleanField("device_enabled", help_text=device_enabled_help)
    owner = models.GenericIPAddressField("device_owner", blank=True, null=True, help_text=device_owner_help)
    allocated = models.BooleanField("device_allocated", help_text=device_allocated_help)
    priority = models.IntegerField("Allocation Priority", default=9999, help_text=allocation_priority_help)

    key = models.CharField('PrimaryKey', db_column='key', primary_key=True, max_length=300,
                           default="%s-%s" % (ip, port), editable=False, unique=True)

    objects = None
