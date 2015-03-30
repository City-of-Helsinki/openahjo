# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0003_auto_20141128_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='confidentiality_reason',
            field=models.CharField(help_text=b'Reason for keeping the attachment confidential', max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
    ]
