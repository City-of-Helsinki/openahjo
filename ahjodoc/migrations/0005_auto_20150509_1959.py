# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0004_attachment_confidentiality_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agendaitem',
            name='issue',
            field=models.ForeignKey(to='ahjodoc.Issue', help_text=b'Issue for the item', null=True),
            preserve_default=True,
        ),
    ]
