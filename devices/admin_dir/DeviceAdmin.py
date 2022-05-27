import os
import threading
from concurrent.futures import ThreadPoolExecutor

from django.utils.html import format_html
from django.contrib import admin
from django.urls import re_path, reverse
from django.http.response import HttpResponseRedirect

from devices.model_dir.Devices import Device
from devices.model_dir.DeviceFunction import DeviceFunction
from devices.common.functions import safe_get_model_all, safe_get_model_by

from devices.admin_dir.common.functions import default_key_switch, default_type_switch, \
    get_all_existing_functions_for_type

from log_config import set_log_level

log = set_log_level()
tpe = ThreadPoolExecutor(max_workers=5)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    readonly_fields = ['device_actions']

    list_display = []
    for key in Device.__dict__.keys():
        if default_key_switch(key):
            continue
        if default_type_switch(type(Device.__dict__[key])):
            list_display.append(str(key))
    list_display.append('device_actions')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r'^function/(?P<device_key>.+)/(?P<function_name>.+)/$',
                self.admin_site.admin_view(self.do_function),
                name='function',
            ),
        ]
        return custom_urls + urls

    def do_function(self, obj, **kwargs):
        device: Device = safe_get_model_by(Device, **{'pk': kwargs.get('device_key')})
        function: DeviceFunction = safe_get_model_by(DeviceFunction, **{'type_association': device.type,
                                                                        'function_name': kwargs.get('function_name')})
        log.debug("          dbg - submitting - run by - pid %s - tid %s" %
                  (os.getpid(), threading.current_thread().ident))
        tpe.submit(function.execute_function, device.pk)
        return HttpResponseRedirect(reverse('admin:devices_device_changelist'))

    def device_actions(self, obj):
        args = []
        button_string = ''
        if obj.type is None:
            return None
        device_function_list: list = get_all_existing_functions_for_type(obj.type.type_def)
        device_function_list.sort(key=str)
        for function in device_function_list:
            button_string += '<a class="button" href="{}">%s</a>&nbsp;' % str(function.function_name)
            args.append(reverse('admin:function', args=[obj.pk, str(function.function_name)]))
        return format_html(button_string, *args)

    device_actions.short_description = 'Device Actions'
    device_actions.allow_tags = True
