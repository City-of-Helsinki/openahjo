# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='policymaker',
            name='type',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
    ]
