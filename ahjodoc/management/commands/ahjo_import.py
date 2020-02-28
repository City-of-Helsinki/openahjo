# -*- coding: utf-8 -*-

import os
import re
import csv
import logging
import datetime
import difflib
import markdown
from optparse import make_option
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from munigeo.models import District
from decisions.models import Organization

from ahjodoc.scanner import AhjoScanner
from ahjodoc.doc import AhjoDocument, ParseError
from ahjodoc.models import *
from ahjodoc.geo import AhjoGeocoder
from ahjodoc.video import get_videos_for_meeting, VideoFile
from ahjodoc.utils import download_file


class Command(BaseCommand):
    help = "Import OpenAHJO documents"
    option_list = BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--meeting-id', dest='meeting_id', action='store', help='import one meeting'),
        make_option('--start-from', dest='start_from', action='store', help='start from provided meeting'),
        make_option('--policymaker-id', dest='policymaker_id', action='store', help='process only provided policymaker'),
        make_option('--full-update', dest='full_update', action='store_true', help='perform full update (i.e. replace existing elements)'),
        make_option('--skip-existing-attachments', dest='skip_existing_attachments', action='store_true',
                    help='do not process existing document attachments'),
        make_option('--no-videos', dest='no_videos', action='store_true', help='do not import meeting videos'),
        make_option('--no-geocoding', dest='no_geocoding', action='store_true', help='do not perform geocoding'),
        make_option('--force-policymakers', dest='force_policymakers', action='store_true', help='force importing of policymakers'),
        make_option('--ignore-attachment-size', dest='ignore-attachment-size', action='store_true', help='disable attachment size checks')
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
        matched_texts = set()

        districts = {}
        for g in geom_list:
            matched_texts.add(g['text'])
            del g['text']
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
            if igeom.type == 'district':
                continue
            # workaround for invalid plan geometry
            if g['type'] == 'plan' and g['name'] == '12079':
                continue
            d_list = District.objects.filter(borders__contains=igeom.geometry)
            for d in d_list:
                districts[d.pk] = d

        issue.districts = districts.values()
        return matched_texts

    def store_keywords(self, issue, text_list):
        for kw in text_list:
            if kw in ['Valtuustoaloite',
                      'Toivomusponnet']:
                kw = kw.lower()
            keyword, _ = IssueKeyword.objects.get_or_create(name=kw)
            issue.keywords.add(keyword)

    def store_issue(self, meeting, meeting_doc, info, adoc):
        try:
            agenda_item = AgendaItem.objects.get(index=info['number'], meeting=meeting)
        except AgendaItem.DoesNotExist:
            agenda_item = AgendaItem(index=info['number'], meeting=meeting)
        agenda_item.subject = info['subject']
        agenda_item.from_minutes = meeting_doc.type == 'minutes'
        agenda_item.origin_last_modified_time = meeting_doc.last_modified_time
        agenda_item.resolution = info.get('resolution')
        agenda_item.preparer = info.get('preparer')
        agenda_item.introducer = info.get('introducer')
        agenda_item.classification_code = info.get('classification_code')
        agenda_item.classification_description = info.get('classification_description')
        agenda_item.issue = None
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

        att_list = Attachment.objects.filter(agenda_item=agenda_item)
        if att_list.count() == 0 or not self.options['skip_existing_attachments']:
            for att in info['attachments']:
                for obj in att_list:
                    if obj.number == att['number']:
                        obj._found = True
                        break
                else:
                    obj = Attachment(agenda_item=agenda_item, number=att['number'])
                    obj._found = True

                if not att['public']:
                    obj.public = False
                    obj.confidentiality_reason = att.get('confidentiality_reason', None)
                    obj.file = None
                    obj.hash = None
                    obj.save()
                    continue
                try:
                    adoc.extract_zip_attachment(att, self.attachment_path)
                except ParseError as e:
                    # Typical case for ParseError is missing attachment, although
                    # it could also be unknown extension or size mismatch with
                    # zipfile metadata
                    # We just log the exception message returned from adoc and move on
                    # FIXME, add status flag for this
                    self.logger.warning(e)
                    continue
                obj.public = True
                obj.file = os.path.join(settings.AHJO_PATHS['attachment'], att['file'])
                obj.file_type = att['type']
                obj.hash = att['hash']
                obj.name = att['name']
                obj.save()

            for obj in att_list:
                if not getattr(obj, '_found', False):
                    self.logger.info("Deleting attachment %s" % obj)
                    obj.delete()

        if not info['register_id']:
            return

        try:
            issue = Issue.objects.get(register_id=info['register_id'])
        except Issue.DoesNotExist:
            issue = Issue(register_id=info['register_id'])

        if not issue.subject:
            issue.subject = info['subject']
        else:
            issue.subject = issue.determine_subject()

        s = info['category']
        m = re.match(r"[\d\s]+", s)
        cat_id = s[0:m.end()].strip()
        category = Category.objects.get(origin_id=cat_id)
        issue.category = category
        issue.reference_text = info.get('reference_text')
        issue.save()

        if agenda_item.issue != issue:
            agenda_item.issue = issue
            agenda_item.save(update_fields=['issue'])

        geo_matches = self.geocode_issue(issue, info)
        text_list = [i for i in info['keywords'] if i not in geo_matches]
        self.store_keywords(issue, text_list)

        latest_date = issue.determine_latest_decision_date()
        if latest_date != issue.latest_decision_date:
            issue.latest_decision_date = latest_date
            issue.save(update_fields=['latest_decision_date'])

    @transaction.commit_on_success
    def import_doc(self, info):
        origin_id = info['origin_id']
        try:
            doc = MeetingDocument.objects.get(origin_id=origin_id)
            if not self.options['full_update'] and doc.last_modified_time >= info['last_modified']:
                if self.verbosity >= 2:
                    self.logger.info("Up-to-date document %s (last modified %s)" % (origin_id, info['last_modified']))
                return
            else:
                print "Re-importing document %s" % origin_id
        except MeetingDocument.DoesNotExist:
            print "Adding new document %s" % origin_id
            doc = MeetingDocument(origin_id=origin_id)

        d = [int(x) for x in info['date'].split('-')]
        doc_date = datetime.date(*d)

        try:
            policymaker = Policymaker.objects.get(origin_id=info['policymaker_id'])
        except Policymaker.DoesNotExist:
            try:
                org = Organization.objects.get(origin_id=info['policymaker_id'])
            except Organization.DoesNotExist:
                print "While trying to create a new policymaker %s, we could not find their organization" % info['policymaker_id']
                print "This happened while trying to import document %s. Ignoring document." % origin_id
                return
            print "Creating new policymaker for %s" % org
            args = {'name': org.name_fi, 'abbreviation': org.abbreviation,
                    'type': org.type, 'origin_id': info['policymaker_id']}
            policymaker = Policymaker(**args)
            policymaker.slug = org.slug
            policymaker.save()
            org.policymaker = policymaker
            org.save(update_fields=['policymaker'])

        if not policymaker.abbreviation and 'policymaker_abbr' in info:
            self.logger.info("Saving abbreviation '%s' for %s" % (info['policymaker_abbr'], policymaker))
            policymaker.abbreviation = info['policymaker_abbr']
            policymaker.save()

        args = {'policymaker': policymaker, 'number': info['meeting_nr'],
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
        doc.policymaker = info['policymaker']
        doc.date = doc_date
        if str(meeting.date) != str(doc.date):
            # If the new meeting date comes from a document with the latest modification
            # time, assume the earlier meeting date is incorrect. Otherwise, bail out.
            latest_doc = meeting.meetingdocument_set.order_by('-last_modified_time')[0]
            if info['last_modified'] > latest_doc.last_modified_time:
                self.logger.warning("Fixing date mismatch between doc and meeting (%s vs. %s)" % (meeting.date, doc.date))
                meeting.date = doc.date
                meeting.save(update_fields=['date'])
            else:
                raise Exception("Date mismatch between doc and meeting (%s vs. %s)" % (meeting.date, doc.date))
        doc.meeting_nr = info['meeting_nr']
        doc.origin_url = info['url']

        adoc = AhjoDocument(verbosity=self.verbosity, options=self.options)
        zipf = self.scanner.download_document(info)
        try:
            adoc.import_from_zip(zipf)
        except ParseError as e:
            self.logger.error("Error importing document %s" % origin_id, exc_info=e)
            self.failed_import_list.append(origin_id)
            raise

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

        register_ids = set()
        for adi in adoc.items:
            register_id = adi.get('register_id', None)
            if register_id is None:
                continue
            if register_id in register_ids:
                self.logger.warning("Issue %s listed more than twice in a meeting" % register_id)
            else:
                register_ids.add(register_id)

        for ai in existing_ais:
            for adi in adoc.items:
                if adi['number'] == ai.index:
                    break
            else:
                self.logger.warning("Agenda item %s not found in incoming items" % ai)
                ai.should_delete = True

            if ai.issue is not None:
                obj_register_id = ai.issue.register_id
            else:
                obj_register_id = None
            if adi.get('register_id', None) != obj_register_id:
                self.logger.warning("Issue mismatch at index %d: %s vs. %s" % (ai.index, adi['register_id'], obj_register_id))
                AgendaItem.objects.filter(meeting=meeting, index__gte=ai.index).delete()
                break

        for ai in existing_ais:
            if getattr(ai, 'should_delete', False):
                self.logger.warning("Deleting stale agenda item %s" % ai)
                ai.delete()

        for issue in adoc.items:
            self.store_issue(meeting, doc, issue, adoc)

        if doc.type == 'minutes':
            meeting.minutes = True
            meeting.save()

        if not self.options['no_videos']:
            self.import_videos(meeting)

    def get_video_screenshot(self, video, video_file):
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
        video_file.take_screenshot(pos, os.path.join(path, fname))
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
        # FIXME: Broken in API
        if meeting.year == 2014 and meeting.number == 3:
            return
        if meeting.year == 2015 and meeting.number == 6:
            return
        if meeting.year == 2015 and meeting.number == 10:
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
        video_file = VideoFile(video_fname)
        video.duration = video_file.get_duration()
        self.get_video_screenshot(video, video_file)
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
            # Remove leading 'Stj / '
            re.sub(r'^[\w]{2,4} / ?', '', title)

            if ai.subject != title:
                db_subj = ai.subject
                if len(title) > 100 and len(db_subj) != len(title):
                    min_len = min(len(db_subj), len(title))
                    title = title[0:min_len]
                    db_subj = db_subj[0:min_len]
                # Attempt a fuzzy match
                matcher = difflib.SequenceMatcher(None, db_subj, title)
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
                self.get_video_screenshot(video, video_file)
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

    def _import_pm_desc(self):
        f = open(os.path.join(self.data_path, 'policymaker.txt'), 'r')
        desc = {}
        active = None
        for l in f.readlines():
            l = l.decode('utf8')
            if l[0] == '[':
                l = l.strip('[]\n')
                desc[l] = []
                active = desc[l]
            else:
                active.append(l.strip())
        for name, lines in desc.items():
            content = '\n'.join(lines).strip()
            if not content:
                del desc[name]
                continue
            content = markdown.markdown(content)
            desc[name] = content
        return desc

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

        desc = self._import_pm_desc()

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
            org_name = org_name.decode('utf8')
            defaults = {'name': org_name}
            pm, c = Policymaker.objects.get_or_create(origin_id=org_id, defaults=defaults)
            if org_name in desc:
                pm.summary = desc[org_name]
                pm.save()
            print "%10s %55s %15s" % (org_id, org_name, ORG_TYPES[int(org_type)])

    def handle(self, **options):
        self.verbosity = int(options['verbosity'])
        self.logger = logging.getLogger(__name__)
        self.options = options
        self.data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        self.geocoder = AhjoGeocoder()

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

        plan_path = os.path.join(self.data_path, 'plans')
        if os.path.isdir(plan_path) and not options['no_geocoding']:
            self.geocoder.load_plans(os.path.join(plan_path, 'Kaava_Vireilla.tab'), in_effect=False)
            self.geocoder.load_plans(os.path.join(plan_path, 'Kaava_Voimassa.tab'), in_effect=True)
            self.geocode_plans = True
        else:
            print "Plan database not found; plan geocoding not available."
            self.geocode_plans = False

        property_path = os.path.join(self.data_path, 'properties')
        if os.path.isdir(property_path) and not options['no_geocoding']:
            self.geocoder.load_plan_units(os.path.join(property_path, 'Kaava_kaavayksikko_Voimassa.tab'))
            self.geocoder.load_properties(os.path.join(property_path, 'kiinteistoalueet.tab'))
            self.geocode_plan_units = True
        else:
            print "Plan unit database not found; plan unit geocoding not available."
            self.geocode_plan_units = False

        addr_fname = os.path.join(self.data_path, 'pks_osoite.csv')
        if os.path.isfile(addr_fname) and not options['no_geocoding']:
            addr_f = open(addr_fname, 'r')
            self.geocoder.load_address_database(addr_f)
            addr_f.close()
            self.geocode_addresses = True
        else:
            print "Address database not found; address geocoding not available."
            self.geocode_addresses = False

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

            #if not 'VH' in info['policymaker_id']:
            #    continue

            if options['policymaker_id'] and \
               info['policymaker_id'].lower() != options['policymaker_id'].lower():
                continue
            self.import_doc(info)
        else:
            if options['meeting_id']:
                print "No meeting document with id '%s' found" % options['meeting_id']
                exit(1)

        if self.geocoder.no_match_addresses:
            s = u"No coordinate match found for addresses:\n"
            for adr in set(self.geocoder.no_match_addresses):
                s += adr.decode('utf8') + '\n'
            self.logger.info(s)
        if self.geocoder.no_match_plans:
            print "No coordinate match found for plans:"
            for plan in self.geocoder.no_match_plans:
                print plan
        if self.failed_import_list:
            print "Importing failed for following documents:"
            for doc in self.failed_import_list:
                print doc
