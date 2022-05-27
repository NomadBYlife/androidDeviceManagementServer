import string
from subprocess import Popen, PIPE

from django.contrib.auth.models import User
from django.db import transaction

from log_config import set_log_level

log = set_log_level()

# unused
"""
def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj
"""


def cleaned_popen_call(command: list):
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    dirty_stdout, dirty_stderr = p.communicate()
    clean_stdout: str = dirty_stdout.strip().decode('ascii', 'replace').strip()
    clean_stderr: str = dirty_stderr.strip().decode('ascii', 'replace').strip()

    printable = set(string.printable)
    clean_stdout = ''.join(filter(lambda x: x in printable, clean_stdout))
    clean_stderr = ''.join(filter(lambda x: x in printable, clean_stderr))

    ret_stdout = clean_stdout.replace("\n[H[J", "")
    ret_stdout = ret_stdout.replace("[H[J", "")
    ret_stderr = clean_stderr.replace("\n[H[J", "")
    ret_stderr = ret_stderr.replace("[H[J", "")

    p.wait()
    ret_exit_code = p.returncode
    return ret_stdout, ret_stderr, ret_exit_code


def safe_get_model_all(model):
    with transaction.atomic():
        ret_val = model.objects.all()
    return ret_val


def safe_get_model_by(model, **kwargs):
    with transaction.atomic():
        ret_val = model.objects.get(**kwargs)
    return ret_val


def safe_set_model_values(model, pk, **kwargs):
    with transaction.atomic():
        instance = model.objects.select_for_update(nowait=False).get(pk=pk)
        for key in kwargs.keys():
            instance.__dict__[key] = kwargs.get(key)
        instance.save()


def safe_delete_all(model):
    with transaction.atomic():
        instances = model.objects.all()
        for instance in instances:
            instance.delete()


def safe_delete_instance(model, pk):
    with transaction.atomic():
        instance = model.objects.get(pk=pk)
        instance.delete()


def safe_create(model, **kwargs):
    with transaction.atomic():
        ret_val = model.objects.create(**kwargs)
    return ret_val


def safe_create_superuser(**kwargs):
    with transaction.atomic():
        ret_val = User.objects.create_superuser(**kwargs)
    return ret_val


def get_dict_from_model(model):
    instance_list = dict()
    for instance in safe_get_model_all(model):
        instance_dict = instance.as_dict()
        key = instance_dict['key']
        instance_list.update({'%s' % key: instance_dict})
    return instance_list


def unsafe_delete_instance(model, pk):
    model.objects.get(pk=pk).delete()


def unsafe_delete_all(model):
    for instance in model.objects.all():
        instance.delete()


def unsafe_get_model_all(model):
    return model.objects.all()


def unsafe_get_instance(model, pk):
    return model.objects.get(pk=pk)


def unsafe_create(model, **kwargs):
    return model.objects.create(**kwargs)

# def unsafe_get_by(model, **kwargs):
#    return model.objects.get(**kwargs)
