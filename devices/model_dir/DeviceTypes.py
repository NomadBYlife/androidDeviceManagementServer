from copy import deepcopy

from django.db import models

from devices.model_dir.common.help_texts import device_type_help

from log_config import set_log_level

log = set_log_level()


class DeviceType(models.Model):
    def __str__(self):
        return self.type_def

    # unused
    """
    @staticmethod
    def get_list():
        tuple_list = []
        try:
            for type_def in safe ... DeviceType):
                tuple_list.append((str(type_def), str(type_def)))
            return tuple_list
        finally:
            return None
    """

    def as_dict(self):
        vars_list = deepcopy(vars(self))
        if '_state' in vars_list.keys():
            vars_list.pop('_state')
        if 'id' in vars_list.keys():
            vars_list.pop('id')
        return vars_list

    def clean(self):
        super(DeviceType, self).clean()

    type_def = models.SlugField("device_type_definition", max_length=200, unique=True, help_text=device_type_help)

    objects = None
