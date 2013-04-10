# -*- coding: utf-8 -*-

import os
import re
import csv
import logging
import datetime
from optparse import make_option
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings

from ahjodoc.scanner import AhjoScanner
from ahjodoc.doc import AhjoDocument
from ahjodoc.models import *

#parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')
#parser.add_argument()

class Command(BaseCommand):
    help = "Import OpenAHJO documents"
    option_list = BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--meeting-id', dest='meeting_id', action='store', help='import one meeting'),
    )

    def store_item(self, meeting, info, is_minutes):
        try:
            item = Item.objects.get(register_id=info['register_id'])
        except Item.DoesNotExist:
            item = Item(register_id=info['register_id'])

        item.subject = info['subject']
        s = info['category']
        m = re.match(r"[\d\s]+", s)
        cat_id = s[0:m.end()].strip()
        category = Category.objects.get(origin_id=cat_id)
        item.category = category
        item.save()

        try:
            agenda_item = AgendaItem.objects.get(item=item, meeting=meeting)
            if not is_minutes:
                # Do not allow items from agenda documents to replace
                # ones from meeting minutes.
                return
        except AgendaItem.DoesNotExist:
            agenda_item = AgendaItem(item=item, meeting=meeting)
        agenda_item.index = info['number']
        agenda_item.from_minutes = is_minutes
        agenda_item.save()

        for idx, p in enumerate(info['content']):
            args = {'agenda_item': agenda_item, 'index': idx}
            try:
                section = ContentSection.objects.get(**args)
            except ContentSection.DoesNotExist:
                section = ContentSection(**args)
            section.type = p[0]
            section.text = '\n'.join(p[1])
            section.save()
        print item.subject

    def import_doc(self, info):
        origin_id = info['origin_id']
        try:
            doc = MeetingDocument.objects.get(origin_id=origin_id)
        except MeetingDocument.DoesNotExist:
            print "Adding new document %s" % origin_id
            doc = MeetingDocument(origin_id=origin_id)
        doc.organisation = info['org']
        doc.committee = info['committee']
        d = [int(x) for x in info['date'].split('-')]
        doc.date = datetime.date(*d)
        doc.meeting_nr = info['meeting_nr']
        doc.origin_url = info['url']

        adoc = AhjoDocument()
        zipf = self.scanner.download_document(info)
        adoc.import_from_zip(zipf)
        zipf.close()
        fname = info['origin_id'] + '.xml'
        print "Storing cleaned XML to %s" % fname
        xmlf = open(os.path.join(self.xml_path, fname), 'w')
        doc.type = adoc.type
        if doc.type == 'agenda':
            assert info['doc_type'] == 'El'
        elif doc.type == 'minutes':
            assert info['doc_type'] == 'Pk'
        adoc.output_cleaned_xml(xmlf)
        xmlf.close()
        doc.xml_file = os.path.join(settings.AHJO_XML_PATH, fname)
        doc.publish_time = adoc.publish_time
        doc.last_modified_time = info['last_modified']
        doc.save()

        committee = Committee.objects.get(origin_id=adoc.committee_id)
        year = doc.date.year
        try:
            meeting = Meeting.objects.get(committee=committee, number=info['meeting_nr'], year=year)
        except Meeting.DoesNotExist:
            meeting = Meeting(committee=committee, number=info['meeting_nr'], year=year)
        meeting.date = doc.date
        if doc.type == 'minutes':
            meeting.minutes = True
        meeting.save()

        for item in adoc.items:
            self.store_item(meeting, item, doc.type == 'minutes')

    def import_categories(self):
        if Category.objects.count():
            return
        f = open(os.path.join(self.data_path, 'categories.csv'), 'r')
        reader = csv.reader(f)
        for row in reader:
            (cat_id, cat_name) = row
            classes = cat_id.split(' ')
            if len(classes) == 1:
                parent = None
            else:
                parent_id = ' '.join(classes[0:-1])
                parent = Category.objects.get(origin_id=parent_id)
            defaults = {'parent': parent, 'name': cat_name}
            cat, c = Category.objects.get_or_create(origin_id=cat_id, defaults=defaults)
            print "%-15s %s" % (cat_id, cat_name)

    def import_committees(self):
        ORG_TYPES = {
            1: 'Valtuusto',
            10: 'Esittelijä',
            11: 'Esittelijä_toimiala',
            12: 'Viranhaltija',
            13: 'Kaupunki',
            2: 'Hallitus',
            3: 'Johtajisto',
            4: 'Jaosto',
            5: 'Lautakunta',
            6: 'Yleinen',
            7: 'Toimiala',
            8: 'Virasto',
            9: 'Osasto',
        }

        if Committee.objects.count():
            return
        f = open(os.path.join(self.data_path, 'organisaatiokoodit.csv'), 'r')
        reader = csv.reader(f)
        # skip header
        reader.next()
        for row in reader:
            (org_id, org_name, org_name_swe, org_type) = row
            if len(org_id) == 3:
                org_id = '00' + org_id
            elif len(org_id) == 4:
                org_id = '0' + org_id
            org_type = int(org_type)
            # Only choose the political committees
            if org_type not in (1, 2, 3, 4, 5):
                continue
            defaults = {'name': org_name}
            comm, c = Committee.objects.get_or_create(origin_id=org_id, defaults=defaults)
            print "%10s %55s %15s" % (org_id, org_name, ORG_TYPES[int(org_type)])

    def handle(self, **options):
        self.data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        self.import_committees()
        self.import_categories()
        self.scanner = AhjoScanner()
        doc_list = self.scanner.scan_documents(cached=options['cached'])
        media_dir = settings.MEDIA_ROOT
        self.scanner.doc_store_path = os.path.join(media_dir, settings.AHJO_ZIP_PATH)
        self.xml_path = os.path.join(media_dir, settings.AHJO_XML_PATH)
        try:
            os.makedirs(self.xml_path)
        except OSError:
            pass
        if options['meeting_id']:
            for info in doc_list:
                if info['origin_id'] == options['meeting_id']:
                    self.import_doc(info)
                    break
            else:
                print "No meeting document with id '%s' found" % options['meeting_id']
                exit(1)
        else:
            for info in doc_list:
                self.import_doc(info)
