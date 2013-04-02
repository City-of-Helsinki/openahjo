# -*- coding: utf-8 -*-

import logging
import datetime
from django.core.management.base import BaseCommand
from django import db

from ahjodoc.scanner import AhjoScanner
from ahjodoc.doc import AhjoDocument
from ahjodoc.models import *

#parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')
#parser.add_argument('--cached', dest='cached', action='store_true', help='cache HTTP requests')

class Command(BaseCommand):
    help = "Import OpenAHJO documents"

    def handle(self, **options):
        scanner = AhjoScanner()
        doc_list = scanner.scan_documents(cached=False)

        for info in doc_list:
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
            doc.save()
