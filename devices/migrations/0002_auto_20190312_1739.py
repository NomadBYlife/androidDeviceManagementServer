# Generated by Django 2.1.7 on 2019-03-12 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='allocated',
            field=models.BooleanField(help_text='If this is True/Set/Checked the device is currently in a claimed state and cannot be claimed by another build agent unless released first.', verbose_name='device_allocated'),
        ),
        migrations.AlterField(
            model_name='device',
            name='description',
            field=models.SlugField(help_text='This is meant to provide information on the use or any special properties of the device.', max_length=200, verbose_name='device_description'),
        ),
        migrations.AlterField(
            model_name='device',
            name='enabled',
            field=models.BooleanField(help_text="If this is True/Set/Checked the device can be claimed by a build agent. (If it is 'On' and not yet claimed). <br>", verbose_name='device_enabled'),
        ),
        migrations.AlterField(
            model_name='device',
            name='owner',
            field=models.GenericIPAddressField(blank=True, help_text='This is the IP/DNS-name of the computer that made the request to claim the device. <br>This may not always be set if this information is not available and is meant for debugging purposes. <br>You should leave this blank in most cases as it will be set automatically. <br>If you manually connect a device to a build agent it makes sense to use this field.', null=True, verbose_name='device_owner'),
        ),
        migrations.AlterField(
            model_name='device',
            name='priority',
            field=models.IntegerField(default=9999, help_text='This value determines the order in which devices are allocated to requests. Low first. High last. If two devices have the same priority value which one will be allocated first is not officially determined although it will have a set order.', verbose_name='Allocation Priority'),
        ),
        migrations.AlterField(
            model_name='device',
            name='status',
            field=models.SlugField(choices=[('---', 'Unknown'), ('ON', 'On'), ('OFF', 'Off'), ('RES', 'Restarting')], default='---', help_text="This should represent the current state of the device. <br>In most cases it should be set automatically if a working 'check_status' function is defined for the device type. <br>If this is not the case it should be set manually to 'On' if its turned on and you expect the device to be available for claiming by a build agent.", max_length=20, verbose_name='device_status'),
        ),
        migrations.AlterField(
            model_name='device',
            name='type',
            field=models.ForeignKey(blank=True, help_text="This represents the name of a group of devices. <br>When trying to claim a device the server is asked a question such as: <br> &nbsp; &nbsp; &nbsp;  Please give me a device of this type: '&lt;Device_type_definition&gt;' <br>The server will then look for any devices of this type which he has configured and return the ip/port of an available device in this group of devices.", null=True, on_delete=django.db.models.deletion.SET_NULL, to='devices.DeviceType', to_field='type_def'),
        ),
        migrations.AlterField(
            model_name='devicefunction',
            name='function_name',
            field=models.SlugField(help_text="The name of the function. <br>This will be displayed as the text for the buttons on the admin pages. <br>A Script with this name with '.sh' attached to the end of it must exist in the appropriate folder on the server. <br>If wanted we can add the functionality to upload the scripts.", max_length=30, verbose_name='device_function_name'),
        ),
        migrations.AlterField(
            model_name='devicefunction',
            name='type_association',
            field=models.ForeignKey(blank=True, help_text="A function can only be defined for a specific type. The function (if the script by that name exists) will only be available for that device type. <br>This was done to allow different types of devices to be handled differently for certain default functions. <br>Default function names: <br> &nbsp; &nbsp; &nbsp;  check_status <br> &nbsp; &nbsp; &nbsp;  restart <br> &nbsp; &nbsp; &nbsp;  start <br> &nbsp; &nbsp; &nbsp;  stop <br><br>The server will call the restart function of a device type on a device every time it is released if the restart function for that device type exists. If it does not exists the step is skipped. <br>Future functionality will start/stop devices on demand. <br><br>The currently implemented default functions for types are: <br> &nbsp; &nbsp; &nbsp;  for cloud-default all default functions <br> &nbsp; &nbsp; &nbsp;  for type-0 'check_status', 'restart' and 'check_params' <br>The functions for type-0 are meant to be used for testing purposes and simply return an exit code and/or the parameters passed to the function, which are determined by the devices current state", null=True, on_delete=django.db.models.deletion.SET_NULL, to='devices.DeviceType', to_field='type_def'),
        ),
        migrations.AlterField(
            model_name='devicetype',
            name='type_def',
            field=models.SlugField(help_text="This represents the name of a group of devices. <br>When trying to claim a device the server is asked a question such as: <br> &nbsp; &nbsp; &nbsp;  Please give me a device of this type: '&lt;Device_type_definition&gt;' <br>The server will then look for any devices of this type which he has configured and return the ip/port of an available device in this group of devices.", max_length=200, unique=True, verbose_name='device_type_definition'),
        ),
    ]