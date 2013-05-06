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
from ahjodoc.doc import AhjoDocument, ParseError
from ahjodoc.models import *
from ahjodoc.geo import AhjoGeocoder

#parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')
#parser.add_argument()

class Command(BaseCommand):
    help = "Import OpenAHJO documents"
    option_list = BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--meeting-id', dest='meeting_id', action='store', help='import one meeting'),
        make_option('--full-update', dest='full_update', action='store_true', help='perform full update (i.e. replace existing elements)'),
    )

    def __init__(self):
        self.failed_import_list = []
        return super(Command, self).__init__()

    def geocode_issue(self, issue, info):
        if not self.geocoder:
            return
        # Attempt to geocode first from subject and keywords.
        # If no matches are found, attempt to geocode from content text.
        text_list = []
        text_list.append(info['subject'])
        for kw in info['keywords']:
            text_list.append(kw)
        markers = self.geocoder.geocode_from_text_list(text_list)
        if not markers:
            pass
        if markers:
            for m in markers:
                try:
                    igeom = IssueGeometry.objects.get(issue=issue, name=m['name'])
                except IssueGeometry.DoesNotExist:
                    igeom = IssueGeometry(issue=issue, name=m['name'])
                igeom.geometry = m['location']
                igeom.save()

    def store_issue(self, meeting, meeting_doc, info, adoc):
        try:
            issue = Issue.objects.get(register_id=info['register_id'])
        except Issue.DoesNotExist:
            issue = Issue(register_id=info['register_id'])

        issue.subject = info['subject']
        print issue.subject
        s = info['category']
        m = re.match(r"[\d\s]+", s)
        cat_id = s[0:m.end()].strip()
        category = Category.objects.get(origin_id=cat_id)
        issue.category = category
        issue.save()

        self.geocode_issue(issue, info)

        try:
            agenda_item = AgendaItem.objects.get(issue=issue, meeting=meeting)
        except AgendaItem.DoesNotExist:
            agenda_item = AgendaItem(issue=issue, meeting=meeting)
        agenda_item.index = info['number']
        agenda_item.from_minutes = meeting_doc.type == 'minutes'
        agenda_item.last_modified_time = meeting_doc.last_modified_time
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

        for att in info['attachments']:
            args = {'agenda_item': agenda_item, 'number': att['number']}
            try:
                obj = Attachment.objects.get(**args)
            except Attachment.DoesNotExist:
                obj = Attachment(**args)
            if not att['public']:
                obj.public = False
                obj.file = None
                obj.hash = None
                obj.save()
                continue
            adoc.extract_zip_attachment(att, self.attachment_path)
            obj.public = True
            obj.file = os.path.join(settings.AHJO_ATTACHMENT_PATH, att['file'])
            obj.file_type = att['type']
            obj.hash = att['hash']
            obj.name = att['name']
            obj.save()

    def import_doc(self, info):
        origin_id = info['origin_id']
        try:
            doc = MeetingDocument.objects.get(origin_id=origin_id)
            if not self.full_update and doc.last_modified_time >= info['last_modified']:
                self.logger.info("Skipping up-to-date document")
                return
        except MeetingDocument.DoesNotExist:
            print "Adding new document %s" % origin_id
            doc = MeetingDocument(origin_id=origin_id)

        d = [int(x) for x in info['date'].split('-')]
        doc_date = datetime.date(*d)

        committee = Committee.objects.get(origin_id=info['committee_id'])
        args = {'committee': committee, 'number': info['meeting_nr'],
                'year': doc_date.year}
        try:
            meeting = Meeting.objects.get(**args)
        except Meeting.DoesNotExist:
            meeting = Meeting(**args)
            meeting.minutes = False
            meeting.date = info['date']
            meeting.save()

        doc.meeting = meeting
        doc.organisation = info['org']
        doc.committee = info['committee']
        doc.date = doc_date
        if str(meeting.date) != str(doc.date):
            raise Exception("Date mismatch between doc and meeting (%s vs. %s)" % (meeting.date, doc.date))
        doc.meeting_nr = info['meeting_nr']
        doc.origin_url = info['url']

        adoc = AhjoDocument()
        zipf = self.scanner.download_document(info)
        try:
            adoc.import_from_zip(zipf)
        except ParseError as e:
            self.logger.error("Error importing document %s" % origin_id, exc_info=e)
            self.failed_import_list.append(origin_id)
            return

        fname = info['origin_id'] + '.xml'
        print "Storing cleaned XML to %s" % fname
        xmlf = open(os.path.join(self.xml_path, fname), 'w')
        doc.type = adoc.type
        if doc.type == 'agenda':
            assert info['doc_type'] == 'agenda'
        elif doc.type == 'minutes':
            assert info['doc_type'] == 'minutes'
        adoc.output_cleaned_xml(xmlf)
        xmlf.close()
        doc.xml_file = os.path.join(settings.AHJO_XML_PATH, fname)
        doc.publish_time = adoc.publish_time
        doc.last_modified_time = info['last_modified']
        doc.save()

        if info['committee_id'] != adoc.committee_id:
            raise Exception("Committee id mismatch (%s vs. %s)" % (info['committee_id'], adoc.committee_id))

        if meeting.minutes and info['doc_type'] == 'agenda':
            self.logger.info("Skipping agenda doc because minutes already exists")
            return

        for issue in adoc.items:
            self.store_issue(meeting, doc, issue, adoc)

        if doc.type == 'minutes':
            meeting.minutes = True
            meeting.save()

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
        self.logger = logging.getLogger(__name__)
        self.full_update = options['full_update']
        self.data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        addr_fname = os.path.join(self.data_path, 'pks_osoite.csv')
        if os.path.isfile(addr_fname):
            addr_f = open(addr_fname, 'r')
            self.geocoder = AhjoGeocoder()
            self.geocoder.load_address_database(addr_f)
            addr_f.close()
        else:
            print "Address database not found; geocoder not available."
            self.geocoder = None

        self.import_committees()
        self.import_categories()
        self.scanner = AhjoScanner()
        doc_list = self.scanner.scan_documents(cached=options['cached'])
        media_dir = settings.MEDIA_ROOT
        self.scanner.doc_store_path = os.path.join(media_dir, settings.AHJO_ZIP_PATH)
        self.xml_path = os.path.join(media_dir, settings.AHJO_XML_PATH)
        self.attachment_path = os.path.join(media_dir, settings.AHJO_ATTACHMENT_PATH)
        try:
            os.makedirs(self.xml_path)
        except OSError:
            pass
        try:
            os.makedirs(self.attachment_path)
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

        if self.geocoder and self.geocoder.no_match_addresses:
            print "No coordinate match found for addresses:"
            for adr in set(self.geocoder.no_match_addresses):
                print adr
        if self.failed_import_list:
            print "Importing failed for following documents:"
            for doc in self.failed_import_list:
                print doc
