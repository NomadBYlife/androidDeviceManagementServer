from devices.model_dir.DeviceTypes import DeviceType
from devices.model_dir.Devices import Device
from devices.model_dir.DeviceFunction import DeviceFunction
from devices.common.functions import unsafe_get_model_all, unsafe_delete_all, unsafe_delete_instance, \
    unsafe_get_instance

from django.db.models.signals import pre_delete, pre_save, post_save
from django.contrib.auth.models import User
from notifications.signals import notify
from notifications.models import Notification
from background_task.models_completed import CompletedTask
from background_task import background
from server_config import background_sleep_time as delay
from server_config import notification_min_time

from log_config import set_log_level

import datetime

log = set_log_level()


def context_refresh(request):
    return {'refresh_val': delay}


# this function is always executed in a different process due to this decorator and py coverage will never see it
@background(schedule=datetime.timedelta(seconds=notification_min_time))
def do_mark_as_read(notice_pk: int):  # other process # pragma: no cover
    i_notice: Notification = unsafe_get_instance(Notification, pk=notice_pk)
    i_notice.mark_as_read()
    # unsafe_delete_notice(Notification, notice_pk)
    unsafe_delete_instance(Notification, notice_pk)


# the following functions are always called from within transactions
# as such opening another transaction which tries to lock the table will cause issues
# for these functions it makes sense to use unsafe database altering methods because they are within transactions
# further up the call stack
# these functions shall not be called otherwise

def fix_function_on_type_delete(sender, **kwargs):
    for device_function in unsafe_get_model_all(DeviceFunction):
        if device_function.type_association == kwargs.get('instance'):
            device_function.fix_deleted_type(sender, **kwargs)


def fix_function_on_type_change(sender, **kwargs):
    for device_function in unsafe_get_model_all(DeviceFunction):
        if device_function.type_association == kwargs.get('instance'):
            device_function.fix_changed_type(sender, **{'device_type': kwargs.get('instance'), **kwargs})


def fix_device_on_type_change(sender, **kwargs):
    for device in unsafe_get_model_all(Device):
        if device.type == kwargs.get('instance'):
            device.fix_on_change(sender, **kwargs)


def update_device(sender, instance: Device, created: bool, **kwargs):
    for user in unsafe_get_model_all(User):
        notice = notify.send(user, recipient=user, verb='Device %s:%s was updated' % (instance.ip, instance.port))
        mark_as_read_in(notice[0][1][0])


def mark_as_read_in(notice: Notification):
    do_mark_as_read(notice.pk)
    # unsafe_delete_all_completed_tasks(CompletedTask)
    unsafe_delete_all(CompletedTask)


pre_delete.connect(fix_function_on_type_delete, sender=DeviceType)

pre_save.connect(fix_function_on_type_change, sender=DeviceType)
pre_save.connect(fix_device_on_type_change, sender=DeviceType)

post_save.connect(update_device, sender=Device)
