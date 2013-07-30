# -*- coding: utf-8 -*-

import os
import re
import csv
import logging
import datetime
import difflib
from optparse import make_option
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings

from ahjodoc.scanner import AhjoScanner
from ahjodoc.doc import AhjoDocument, ParseError
from ahjodoc.models import *
from ahjodoc.geo import AhjoGeocoder
from ahjodoc.video import get_videos_for_meeting, open_video, get_video_frame
from ahjodoc.utils import download_file

#parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')
#parser.add_argument()

class Command(BaseCommand):
    help = "Import OpenAHJO documents"
    option_list = BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--meeting-id', dest='meeting_id', action='store', help='import one meeting'),
        make_option('--start-from', dest='start_from', action='store', help='start from provided meeting'),
        make_option('--policymaker-id', dest='policymaker_id', action='store', help='process only provided policymaker'),
        make_option('--full-update', dest='full_update', action='store_true', help='perform full update (i.e. replace existing elements)'),
        make_option('--no-attachments', dest='no_attachments', action='store_true', help='do not process document attachments'),
        make_option('--no-videos', dest='no_videos', action='store_true', help='do not import meeting videos'),
        make_option('--force-policymakers', dest='force_policymakers', action='store_true', help='force importing of policymakers'),
    )

    def __init__(self):
        self.failed_import_list = []
        return super(Command, self).__init__()

    def geocode_issue(self, issue, info):
        # Attempt to geocode first from subject and keywords.
        # If no matches are found, attempt to geocode from content text.
        text_list = []
        text_list.append(info['subject'])
        for kw in info['keywords']:
            text_list.append(kw)
        geom_list = self.geocoder.geocode_from_text_list(text_list)
        for g in geom_list:
            args = dict(type=g['type'], name=g['name'])
            try:
                igeom = IssueGeometry.objects.get(**args)
            except IssueGeometry.DoesNotExist:
                args['geometry'] = g['geometry']
                igeom = IssueGeometry(**args)
                igeom.save()
            issue.geometries.add(igeom)
            # Assume geometry doesn't change.
            #igeom.geometry = g['geometry']
            #igeom.save()

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
        agenda_item.subject = info['subject']
        agenda_item.index = info['number']
        agenda_item.from_minutes = meeting_doc.type == 'minutes'
        agenda_item.last_modified_time = meeting_doc.last_modified_time
        agenda_item.resolution = info.get('resolution')
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

        if self.options['no_attachments']:
            return
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
            obj.file = os.path.join(settings.AHJO_PATHS['attachment'], att['file'])
            obj.file_type = att['type']
            obj.hash = att['hash']
            obj.name = att['name']
            obj.save()

    def import_doc(self, info):
        origin_id = info['origin_id']
        try:
            doc = MeetingDocument.objects.get(origin_id=origin_id)
            if not self.options['full_update'] and doc.last_modified_time >= info['last_modified']:
                self.logger.info("Up-to-date document %s (last modified %s)" % (origin_id, info['last_modified']))
                return
            else:
                print "Re-importing document %s" % origin_id
        except MeetingDocument.DoesNotExist:
            print "Adding new document %s" % origin_id
            doc = MeetingDocument(origin_id=origin_id)

        d = [int(x) for x in info['date'].split('-')]
        doc_date = datetime.date(*d)

        policymaker = Policymaker.objects.get(origin_id=info['policymaker_id'])
        args = {'policymaker': policymaker, 'number': info['meeting_nr'],
                'year': doc_date.year}
        if not policymaker.abbreviation and 'policymaker_abbr' in info:
            self.logger.info("Saving abbreviation '%s' for %s" % (info['policymaker_abbr'], policymaker))
            policymaker.abbreviation = info['policymaker_abbr']
            policymaker.save()
        try:
            meeting = Meeting.objects.get(**args)
        except Meeting.DoesNotExist:
            meeting = Meeting(**args)
            meeting.minutes = False
            meeting.date = info['date']
            meeting.save()

        doc.meeting = meeting
        doc.organisation = info['org']
        doc.policymaker = info['policymaker']
        doc.date = doc_date
        if str(meeting.date) != str(doc.date):
            raise Exception("Date mismatch between doc and meeting (%s vs. %s)" % (meeting.date, doc.date))
        doc.meeting_nr = info['meeting_nr']
        doc.origin_url = info['url']

        adoc = AhjoDocument(verbosity=self.verbosity)
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
        doc.xml_file = os.path.join(settings.AHJO_PATHS['xml'], fname)
        doc.publish_time = adoc.publish_time
        doc.last_modified_time = info['last_modified']
        doc.save()

        if info['policymaker_id'] != adoc.policymaker_id:
            raise Exception("Policymaker id mismatch (%s vs. %s)" % (info['policymaker_id'], adoc.policymaker_id))

        if meeting.minutes and info['doc_type'] == 'agenda':
            self.logger.info("Skipping agenda doc because minutes already exists")
            return

        # Perform some sanity checks.
        existing_ais = AgendaItem.objects.filter(meeting=meeting).order_by('index')
        if existing_ais.count() > len(adoc.items):
            self.logger.warning("More agenda items in DB (%d) than in document (%d)" % (existing_ais.count(), len(adoc.items)))
            existing_ais.delete()
        for idx, ai in enumerate(existing_ais):
            adi = adoc.items[idx]
            if adi['register_id'] == ai.issue.register_id and adi['number'] == ai.index:
                continue
            self.logger.warning("Issue mismatch at index %d: %s vs. %s" % (idx, adi['register_id'], ai.issue.register_id))
            AgendaItem.objects.filter(meeting=meeting, index__gte=ai.index).delete()
            break

        for issue in adoc.items:
            self.store_issue(meeting, doc, issue, adoc)

        if doc.type == 'minutes':
            meeting.minutes = True
            meeting.save()

        if not self.options['no_videos']:
            self.import_videos(meeting)

    def get_video_screenshot(self, video, video_stream):
        meeting_id = '%d-%d' % (video.meeting.number, video.meeting.year)
        path = os.path.join(self.video_path, meeting_id)
        if not os.path.exists(path):
            os.makedirs(path)
        if not video.agenda_item:
            fname = 'meeting.jpg'
            # Take screenshot at 4 minutes
            pos = 240
        else:
            fname = 'item%d-%d.jpg' % (video.agenda_item.index, video.index)
            pos = video.start_pos + video.duration / 2.0

        self.logger.debug("Fetching screenshot as %s" % fname)
        ss_img = get_video_frame(video_stream, pos)
        ss_img.save(os.path.join(path, fname))
        video.screenshot = os.path.join(settings.AHJO_PATHS['video'], meeting_id, fname)

    def download_video(self, url):
        fname = url.split('/')[-1]
        path = os.path.join(self.video_path, fname)
        if not os.path.exists(path):
            self.logger.debug("Downloading video at %s" % url)
            download_file(url, path)
        return path

    def import_videos(self, meeting):
        # Only Kaupunginvaltuusto supported for now.
        if meeting.policymaker.origin_id != '02900':
            return
        self.logger.debug("Checking for videos for %s" % meeting)
        meeting_info = {'year': meeting.year, 'nr': meeting.number}
        video_info = get_videos_for_meeting(meeting_info)
        if not video_info:
            return
        try:
            video = Video.objects.get(meeting=meeting, agenda_item=None)
        except Video.DoesNotExist:
            video = Video(meeting=meeting, agenda_item=None)
        video.start_pos = 0
        video.speaker = None
        video.index = 0
        video.url = video_info['video']['http_url']

        video_fname = self.download_video(video.url)
        video_stream = open_video(video_fname)
        video.duration = video_stream.duration
        self.get_video_screenshot(video, video_stream)
        video.save()
        ai_list = AgendaItem.objects.filter(meeting=meeting).order_by('index')
        if self.verbosity >= 2:
            # DEBUG
            print "Video"
            titles = ["%s. %s" % (i['id'], i['title']) for i in video_info['issues']]
            for t in titles: print "\t" + t

            print "Ahjo"
            titles = ["%s. %s" % (i.index, i.subject) for i in ai_list]
            for t in titles: print "\t" + t

        for idx, issue in enumerate(video_info['issues']):
            agenda_index = issue['id']
            # Skip subsections (like question hour)
            if '.' in agenda_index:
                #agenda_index = agenda_index.split('.')[0]
                continue
            agenda_index = int(agenda_index)
            for ai in ai_list:
                if ai.index == agenda_index:
                    break
            else:
                self.logger.info(u"No agenda item found for issue: %s" % issue['title'])
                continue
            title = issue['title'].strip()
            if ai.subject != title:
                # Attempt a fuzzy match
                matcher = difflib.SequenceMatcher(None, ai.subject, title)
                if matcher.ratio() < 0.90:
                    self.logger.error(u"Mismatch between titles: '%s' vs. '%s'" % (ai.subject, title))
                    raise Exception("Title mismatch")
            vid_list = [{'start_pos': issue['video_position'], 'speaker': None, 'party': None}]
            for statement in issue['statements']:
                vid = {'start_pos': statement['video_position'], 'duration': statement['duration']}
                vid['speaker'] = statement['participant']['name']
                vid['party'] = statement['participant']['party']
                vid_list.append(vid)
            for idx, vid_info in enumerate(vid_list):
                args = dict(meeting=meeting, agenda_item=ai, index=idx)
                try:
                    video = Video.objects.get(**args)
                except Video.DoesNotExist:
                    video = Video(**args)
                video.url = video.url
                video.speaker = vid_info['speaker']
                video.start_pos = vid_info['start_pos']
                video.party = vid_info['party']
                video.url = video_info['video']['http_url']
                if 'duration' in vid_info:
                    video.duration = vid_info['duration']
                else:
                    if idx < len(vid_list) - 1:
                        video.duration = vid_list[idx+1]['start_pos'] - video.start_pos
                    else:
                        video.duration = 0
                self.get_video_screenshot(video, video_stream)
                video.save()

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

    def import_policymakers(self):
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

        if not self.options['force_policymakers'] and Policymaker.objects.count():
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
            # Only choose the political policymakers
            if org_type not in (1, 2, 3, 4, 5):
                continue
            defaults = {'name': org_name}
            comm, c = Policymaker.objects.get_or_create(origin_id=org_id, defaults=defaults)
            print "%10s %55s %15s" % (org_id, org_name, ORG_TYPES[int(org_type)])

    def handle(self, **options):
        self.verbosity = int(options['verbosity'])
        self.logger = logging.getLogger(__name__)
        self.options = options
        self.data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        self.geocoder = AhjoGeocoder()

        plan_path = os.path.join(self.data_path, 'plans')
        if os.path.isdir(plan_path):
            self.geocoder.load_plans(os.path.join(plan_path, 'Kaava_vir_rajaus.TAB'))
            self.geocoder.load_plans(os.path.join(plan_path, 'Lv_rajaus.TAB'))
            self.geocode_plans = True
        else:
            print "Plan database not found; plan geocoding not available."
            self.geocode_plans = False

        addr_fname = os.path.join(self.data_path, 'pks_osoite.csv')
        if os.path.isfile(addr_fname):
            addr_f = open(addr_fname, 'r')
            self.geocoder.load_address_database(addr_f)
            addr_f.close()
            self.geocode_addresses = True
        else:
            print "Address database not found; address geocoding not available."
            self.geocode_addresses = False

        self.import_policymakers()
        self.import_categories()
        self.scanner = AhjoScanner(verbosity=self.verbosity)
        doc_list = self.scanner.scan_documents(cached=options['cached'])
        media_dir = settings.MEDIA_ROOT
        self.scanner.doc_store_path = os.path.join(media_dir, settings.AHJO_PATHS['zip'])
        self.xml_path = os.path.join(media_dir, settings.AHJO_PATHS['xml'])
        self.attachment_path = os.path.join(media_dir, settings.AHJO_PATHS['attachment'])
        self.video_path = os.path.join(media_dir, settings.AHJO_PATHS['video'])
        for path in (self.xml_path, self.attachment_path, self.video_path):
            if not os.path.exists(path):
                os.makedirs(path)

        for info in doc_list:
            if options['meeting_id']:
                if info['origin_id'] == options['meeting_id']:
                    self.import_doc(info)
                    break
                else:
                    continue

            if options['start_from']:
                if options['start_from'] == info['origin_id']:
                    options['start_from'] = ''
                else:
                    continue

            if options['policymaker_id'] and info['policymaker_id'] != options['policymaker_id']:
                continue
            self.import_doc(info)
        else:
            if options['meeting_id']:
                print "No meeting document with id '%s' found" % options['meeting_id']
                exit(1)

        if self.geocoder.no_match_addresses:
            print "No coordinate match found for addresses:"
            for adr in set(self.geocoder.no_match_addresses):
                print adr
        if self.geocoder.no_match_plans:
            print "No coordinate match found for plans:"
            for plan in self.geocoder.no_match_plans:
                print plan
        if self.failed_import_list:
            print "Importing failed for following documents:"
            for doc in self.failed_import_list:
                print doc
