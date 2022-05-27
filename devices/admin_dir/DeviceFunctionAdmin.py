from django.contrib import admin

from devices.model_dir.DeviceFunction import DeviceFunction

from devices.admin_dir.common.functions import default_type_switch, default_key_switch


@admin.register(DeviceFunction)
class DeviceFunctionAdmin(admin.ModelAdmin):
    list_display = []
    for key in DeviceFunction.__dict__.keys():
        if default_key_switch(key):
            continue
        if default_type_switch(type(DeviceFunction.__dict__[key])):
            list_display.append(str(key))
