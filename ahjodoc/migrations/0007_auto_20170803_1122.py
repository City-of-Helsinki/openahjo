# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0006_auto_20150510_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meetingdocument',
            name='origin_url',
            field=models.URLField(help_text=b'Link to the upstream file', max_length=300),
            preserve_default=True,
        ),
    ]
