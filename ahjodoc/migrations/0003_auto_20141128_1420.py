# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0002_policymaker_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='policymaker',
            name='department',
            field=models.CharField(default='', help_text=b'Policymaker department', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='policymaker',
            name='division',
            field=models.CharField(default='', help_text=b'Policymaker division', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='policymaker',
            name='unit',
            field=models.CharField(default='', help_text=b'Policymaker unit', max_length=100),
            preserve_default=False,
        ),
    ]
