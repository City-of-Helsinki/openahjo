# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('decisions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='type',
            field=models.CharField(default='', max_length=30, choices=[(b'council', 'Council'), (b'board', 'Board'), (b'board_division', 'Board division'), (b'committee', 'Committee'), (b'field', 'Field'), (b'department', 'Department'), (b'division', 'Division'), (b'introducer', 'Introducer'), (b'introducer_field', 'Introducer (Field)'), (b'office_holder', 'Office holder'), (b'city', 'City'), (b'unit', 'Unit')]),
            preserve_default=False,
        ),
    ]
