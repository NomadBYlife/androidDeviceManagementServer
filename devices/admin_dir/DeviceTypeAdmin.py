from django.contrib import admin

from devices.model_dir.DeviceTypes import DeviceType

from devices.admin_dir.common.functions import default_type_switch, default_key_switch


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = []
    for key in DeviceType.__dict__.keys():
        if default_key_switch(key):
            continue
        if default_type_switch(type(DeviceType.__dict__[key])):
            list_display.append(str(key))
