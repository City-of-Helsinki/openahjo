# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0005_auto_20150509_1959'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='agendaitem',
            unique_together=set([('meeting', 'index')]),
        ),
    ]
