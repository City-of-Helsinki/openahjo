# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields
import popolo.behaviors.models
import autoslug.fields
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A label describing the membership', max_length=128, null=True, verbose_name='label', blank=True)),
                ('role', models.CharField(help_text='The role that the person fulfills in the organization', max_length=128, null=True, verbose_name='role', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MembershipContactDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A human-readable label for the contact detail', max_length=128, null=True, verbose_name='label', blank=True)),
                ('contact_type', models.CharField(help_text="A type of medium, e.g. 'fax' or 'email'", max_length=12, verbose_name='type', choices=[(b'FAX', 'Fax'), (b'PHONE', 'Telephone'), (b'MOBILE', 'Mobile'), (b'EMAIL', 'Email'), (b'MAIL', 'Snail mail'), (b'TWITTER', 'Twitter'), (b'FACEBOOK', 'Facebook')])),
                ('value', models.CharField(help_text='A value, e.g. a phone number or email address', max_length=128, verbose_name='value')),
                ('note', models.CharField(help_text='A note, e.g. for grouping contact details by physical location', max_length=128, null=True, verbose_name='note', blank=True)),
                ('membership', models.ForeignKey(related_name='contact_details', to='decisions.Membership')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MembershipLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('membership', models.ForeignKey(related_name='links', to='decisions.Membership')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MembershipSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('membership', models.ForeignKey(related_name='sources', to='decisions.Membership')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('name', models.CharField(help_text='A primary name, e.g. a legally recognized name', max_length=128, verbose_name='name')),
                ('name_fi', models.CharField(help_text='A primary name, e.g. a legally recognized name', max_length=128, null=True, verbose_name='name')),
                ('name_sv', models.CharField(help_text='A primary name, e.g. a legally recognized name', max_length=128, null=True, verbose_name='name')),
                ('classification', models.CharField(help_text='An organization category, e.g. committee', max_length=128, null=True, verbose_name='classification', blank=True)),
                ('dissolution_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'dissolution date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$', code=b'invalid_dissolution_date')], max_length=10, blank=True, help_text='A date of dissolution', null=True, verbose_name='dissolution date')),
                ('founding_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'founding date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$', code=b'invalid_founding_date')], max_length=10, blank=True, help_text='A date of founding', null=True, verbose_name='founding date')),
                ('id', models.CharField(max_length=50, serialize=False, primary_key=True)),
                ('origin_id', models.CharField(max_length=50, db_index=True)),
                ('abbreviation', models.CharField(max_length=20)),
                ('deleted', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(to='decisions.Organization', help_text='The ID of the organization that contains this organization', null=True)),
                ('parents', models.ManyToManyField(related_name='all_children', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationContactDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A human-readable label for the contact detail', max_length=128, null=True, verbose_name='label', blank=True)),
                ('contact_type', models.CharField(help_text="A type of medium, e.g. 'fax' or 'email'", max_length=12, verbose_name='type', choices=[(b'FAX', 'Fax'), (b'PHONE', 'Telephone'), (b'MOBILE', 'Mobile'), (b'EMAIL', 'Email'), (b'MAIL', 'Snail mail'), (b'TWITTER', 'Twitter'), (b'FACEBOOK', 'Facebook')])),
                ('value', models.CharField(help_text='A value, e.g. a phone number or email address', max_length=128, verbose_name='value')),
                ('note', models.CharField(help_text='A note, e.g. for grouping contact details by physical location', max_length=128, null=True, verbose_name='note', blank=True)),
                ('postcode', models.CharField(max_length=10)),
                ('organization', models.ForeignKey(related_name='contact_details', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationIdentifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(help_text='An issued identifier, e.g. a DUNS number', max_length=128, verbose_name='identifier')),
                ('scheme', models.CharField(help_text='An identifier scheme, e.g. DUNS', max_length=128, null=True, verbose_name='scheme', blank=True)),
                ('organization', models.ForeignKey(related_name='identifiers', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('organization', models.ForeignKey(related_name='links', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationOtherName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('name', models.CharField(help_text='An alternate or former name', max_length=128, verbose_name='name')),
                ('note', models.CharField(help_text="A note, e.g. 'Birth name'", max_length=256, null=True, verbose_name='note', blank=True)),
                ('organization', models.ForeignKey(related_name='other_names', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('organization', models.ForeignKey(related_name='sources', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('name', models.CharField(help_text="A person's preferred full name", max_length=128, verbose_name='name')),
                ('family_name', models.CharField(help_text='One or more family names', max_length=128, null=True, verbose_name='family name', blank=True)),
                ('given_name', models.CharField(help_text='One or more primary given names', max_length=128, null=True, verbose_name='given name', blank=True)),
                ('additional_name', models.CharField(help_text='One or more secondary given names', max_length=128, null=True, verbose_name='additional name', blank=True)),
                ('honorific_prefix', models.CharField(help_text="One or more honorifics preceding a person's name", max_length=128, null=True, verbose_name='honorific prefix', blank=True)),
                ('honorific_suffix', models.CharField(help_text="One or more honorifics following a person's name", max_length=128, null=True, verbose_name='honorific suffix', blank=True)),
                ('patronymic_name', models.CharField(help_text='One or more patronymic names', max_length=128, null=True, verbose_name='patronymic name', blank=True)),
                ('sort_name', models.CharField(help_text='A name to use in an lexicographically ordered list', max_length=128, null=True, verbose_name='sort name', blank=True)),
                ('email', models.EmailField(help_text='A preferred email address', max_length=75, null=True, verbose_name='email', blank=True)),
                ('gender', models.IntegerField(blank=True, help_text='A gender', null=True, verbose_name='gender', choices=[(0, 'Female'), (1, 'Male')])),
                ('birth_date', models.CharField(help_text='A date of birth', max_length=10, null=True, verbose_name='birth date', blank=True)),
                ('death_date', models.CharField(help_text='A date of death', max_length=10, null=True, verbose_name='death date', blank=True)),
                ('summary', models.CharField(help_text="A one-line account of a person's life", max_length=512, null=True, verbose_name='summary', blank=True)),
                ('biography', models.TextField(help_text="An extended account of a person's life", null=True, verbose_name='biography', blank=True)),
                ('image', models.URLField(help_text='A URL of a head shot', null=True, verbose_name='image', blank=True)),
                ('origin_id', models.CharField(max_length=50, db_index=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonContactDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A human-readable label for the contact detail', max_length=128, null=True, verbose_name='label', blank=True)),
                ('contact_type', models.CharField(help_text="A type of medium, e.g. 'fax' or 'email'", max_length=12, verbose_name='type', choices=[(b'FAX', 'Fax'), (b'PHONE', 'Telephone'), (b'MOBILE', 'Mobile'), (b'EMAIL', 'Email'), (b'MAIL', 'Snail mail'), (b'TWITTER', 'Twitter'), (b'FACEBOOK', 'Facebook')])),
                ('value', models.CharField(help_text='A value, e.g. a phone number or email address', max_length=128, verbose_name='value')),
                ('note', models.CharField(help_text='A note, e.g. for grouping contact details by physical location', max_length=128, null=True, verbose_name='note', blank=True)),
                ('person', models.ForeignKey(related_name='contact_details', to='decisions.Person')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonIdentifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(help_text='An issued identifier, e.g. a DUNS number', max_length=128, verbose_name='identifier')),
                ('scheme', models.CharField(help_text='An identifier scheme, e.g. DUNS', max_length=128, null=True, verbose_name='scheme', blank=True)),
                ('person', models.ForeignKey(related_name='identifiers', to='decisions.Person')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('person', models.ForeignKey(related_name='links', to='decisions.Person')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonOtherName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('name', models.CharField(help_text='An alternate or former name', max_length=128, verbose_name='name')),
                ('note', models.CharField(help_text="A note, e.g. 'Birth name'", max_length=256, null=True, verbose_name='note', blank=True)),
                ('person', models.ForeignKey(related_name='other_names', to='decisions.Person')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('person', models.ForeignKey(related_name='sources', to='decisions.Person')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('label', models.CharField(help_text='A label describing the post', max_length=128, verbose_name='label')),
                ('role', models.CharField(help_text='The function that the holder of the post fulfills', max_length=128, null=True, verbose_name='role', blank=True)),
                ('organization', models.ForeignKey(related_name='posts', to='decisions.Organization', help_text='The organization in which the post is held')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PostContactDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A human-readable label for the contact detail', max_length=128, null=True, verbose_name='label', blank=True)),
                ('contact_type', models.CharField(help_text="A type of medium, e.g. 'fax' or 'email'", max_length=12, verbose_name='type', choices=[(b'FAX', 'Fax'), (b'PHONE', 'Telephone'), (b'MOBILE', 'Mobile'), (b'EMAIL', 'Email'), (b'MAIL', 'Snail mail'), (b'TWITTER', 'Twitter'), (b'FACEBOOK', 'Facebook')])),
                ('value', models.CharField(help_text='A value, e.g. a phone number or email address', max_length=128, verbose_name='value')),
                ('note', models.CharField(help_text='A note, e.g. for grouping contact details by physical location', max_length=128, null=True, verbose_name='note', blank=True)),
                ('post', models.ForeignKey(related_name='contact_details', to='decisions.Post')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PostLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('post', models.ForeignKey(related_name='links', to='decisions.Post')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PostSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=128, null=True, verbose_name='note', blank=True)),
                ('post', models.ForeignKey(related_name='sources', to='decisions.Post')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='membership',
            name='on_behalf_of',
            field=models.ForeignKey(related_name='memberships_on_behalf_of', to='decisions.Organization', help_text='The organization on whose behalf the person is a party to the relationship'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='membership',
            name='organization',
            field=models.ForeignKey(related_name='memberships', to='decisions.Organization', help_text='The organization that is a party to the relationship'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='membership',
            name='person',
            field=models.ForeignKey(related_name='memberships', to='decisions.Person', help_text='The person who is a party to the relationship'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='membership',
            name='post',
            field=models.ForeignKey(related_name='memberships', to='decisions.Post', help_text='The post held by the person in the organization through this membership', null=True),
            preserve_default=True,
        ),
    ]
