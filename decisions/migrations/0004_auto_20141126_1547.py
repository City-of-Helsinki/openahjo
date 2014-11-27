# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('decisions', '0003_organization_policymaker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='policymaker',
            field=models.OneToOneField(related_name='organization', null=True, to='ahjodoc.Policymaker'),
            preserve_default=True,
        ),
    ]
