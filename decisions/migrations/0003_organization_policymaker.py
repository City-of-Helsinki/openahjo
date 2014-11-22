# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjodoc', '0002_policymaker_type'),
        ('decisions', '0002_organization_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='policymaker',
            field=models.ForeignKey(to='ahjodoc.Policymaker', null=True),
            preserve_default=True,
        ),
    ]
