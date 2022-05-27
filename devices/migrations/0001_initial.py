# Generated by Django 2.1.7 on 2019-02-25 16:54

import devices.model_dir.common.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('ip', models.GenericIPAddressField(verbose_name='device_ip')),
                ('port', models.IntegerField(validators=[devices.model_dir.common.validators.validate_port_range], verbose_name='device_port')),
                ('description', models.SlugField(max_length=200, verbose_name='device_description')),
                ('status', models.SlugField(choices=[('---', 'Unknown'), ('ON', 'On'), ('OFF', 'Off'), ('RES', 'Restarting')], default='---', max_length=20, verbose_name='device_status')),
                ('enabled', models.BooleanField(verbose_name='device_enabled')),
                ('owner', models.GenericIPAddressField(blank=True, null=True, verbose_name='device_owner')),
                ('allocated', models.BooleanField(verbose_name='device_allocated')),
                ('priority', models.IntegerField(default=9999, verbose_name='Allocation Priority')),
                ('key', models.CharField(db_column='key', default='<django.db.models.fields.GenericIPAddressField>-<django.db.models.fields.IntegerField>', editable=False, max_length=300, primary_key=True, serialize=False, unique=True, verbose_name='PrimaryKey')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceFunction',
            fields=[
                ('function_name', models.SlugField(max_length=30, verbose_name='device_function_name')),
                ('script_path', models.SlugField(blank=True, default=None, editable=False, max_length=300, null=True, verbose_name='script_path')),
                ('script_found', models.BooleanField(default=False, editable=False, verbose_name='script_found')),
                ('key', models.CharField(db_column='key', default='<django.db.models.fields.related.ForeignKey>-<django.db.models.fields.SlugField>', editable=False, max_length=300, primary_key=True, serialize=False, unique=True, verbose_name='PrimaryKey')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_def', models.SlugField(max_length=200, unique=True, verbose_name='device_type_definition')),
            ],
        ),
        migrations.AddField(
            model_name='devicefunction',
            name='type_association',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='devices.DeviceType', to_field='type_def'),
        ),
        migrations.AddField(
            model_name='device',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='devices.DeviceType', to_field='type_def'),
        ),
    ]
