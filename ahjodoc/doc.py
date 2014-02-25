# -*- coding: utf-8 -*-
import os
import re
import hashlib
from lxml import etree, html, objectify
import zipfile
import logging
import tempfile
from pytz import timezone
from datetime import datetime

local_timezone = timezone('EET')

class ParseError(Exception):
    pass

def clean_text(text):
    text = text.replace('\n', ' ')
    # remove consecutive whitespaces
    return re.sub(r'\s\s+', ' ', text, re.U).strip()

class AhjoDocument(object):
    ATTACHMENT_EXTS = ('pdf', 'xls', 'ppt', 'doc', 'docx', 'png')

    def __init__(self, verbosity=1, options={}):
        self.verbosity = verbosity
        self.options = options
        self.logger = logging.getLogger(__name__)
        pass

    def clean_xml(self):
        root = self.xml_root
        REMOVE_LIST = ('Logo', 'MuutoksenhakuohjeetSektio', 'AlatunnisteSektio')
        for el_name in REMOVE_LIST:
            el_list = root.xpath("//%s" % el_name)
            for el in el_list:
                el.clear()

        def is_empty(el):
            for val in el.values():
                if val:
                    return False
            if el.text and el.text.strip():
                return False
            if el.tail and el.tail.strip():
                return False
            if el.getchildren():
                    return False
            return True

        def remove_empty_children(el):
            for ch in el.iterchildren():
                # Skip the HTML containers
                if el.tag == 'XHTML':
                    continue
                remove_empty_children(ch)
                if is_empty(ch):
                    el.remove(ch)

        remove_empty_children(root)

    def parse_header_info(self):
        desc_info = self.xml_root.xpath('//Kuvailutiedot/JulkaisuMuutostiedot')[0]
        # WORKAROUND: remove spaces from date and time
        date = desc_info.find('JulkaisuEsilletulopaiva').text.replace(' ', '')
        time = desc_info.find('JulkaisuEsilletuloklo').text.replace(' ', '')
        time_str = "%s %s" % (date, time)
        self.publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M').replace(tzinfo=local_timezone)

        policymaker_el = self.xml_root.xpath('./YlatunnisteSektio/Paattaja')[0]
        self.policymaker_id = policymaker_el.attrib['PaattajaId']

    def parse_text_section(self, section_el):
        children = section_el.getchildren()
        content = []
        for ch in children:
            if ch.tag != 'taso1':
                raise ParseError("Unexpected text section container: %s" % ch.tag)
            paras = ch.getchildren()
            for p in paras:
                if p.tag not in ('Kappale', 'Otsikko', 'Henkilotietoa', 'Salassapidettava', 'XHTML', 'HenkilotietoaXHTML', 'Kuva'):
                    raise ParseError("Unsupported paragraph tag: %s", p.tag)
                if p.tag == 'Kappale':
                    for pch in p.getchildren():
                        if pch.tag == 'KappaleOptiot':
                            # FIXME
                            continue
                        if pch.tag != 'KappaleTeksti':
                            raise ParseError("Unsupported paragraph text tag: %s" % pch.tag)
                        text = pch.text
                        assert not pch.getchildren()
                        tail = pch.tail.strip()
                        assert not tail
                        content.append(u'<p>%s</p>' % clean_text(text))
                elif p.tag == 'Otsikko':
                    if not p.text:
                        continue
                    content.append(u'<h3>%s</h3>' % clean_text(p.text))
                elif p.tag in ('Henkilotietoa', 'HenkilotietoaXHTML'):
                    content.append(u'<span class="redacted-personal-information">*****</span>')
                elif p.tag == 'Salassapidettava':
                    content.append(u'<p class="redacted-information">*****</p>')
                elif p.tag == 'XHTML':
                    html_str = ''
                    for pch in p.getchildren():
                        html_el = html.fromstring(etree.tostring(pch))
                        etree.strip_tags(html_el, 'font', 'span')
                        for child_el in html_el.getiterator():
                            if 'style' in child_el.attrib:
                                del child_el.attrib['style']
                        for attr in html_el.attrib:
                            if attr.startswith('xmlns'):
                                del html_el.attrib[attr]
                        s = etree.tostring(html_el, encoding='utf8', method='html')
                        html_str += clean_text(s.decode('utf8'))
                    content.append(html_str)
        return content

    SECTION_TYPES = {
        'paatosehdotus': 'draft resolution',
        'esitysehdotus': 'draft resolution', # FIXME verify this
        'paatoksenperustelut': 'reasons for resolution',
        'tiivistelma': 'summary',
        'esittelija': 'presenter',
        'paatos': 'resolution',
        'kasittely': 'hearing',
    }
    def parse_item_content(self, info, item_el):
        section_el_list = item_el.xpath('./SisaltoSektioToisto/SisaltoSektio')
        content = []
        for section_el in section_el_list:
            s = section_el.attrib.get('sisaltosektioTyyppi')
            if not s:
                self.logger.warning("attribute sisaltosektioTyyppi not found")
                subj_el = section_el.find('SisaltoOtsikko')
                if not subj_el:
                    continue
                s = subj_el.attrib['SisaltoOtsikkoTyyppi']
                if not s:
                    continue
            if s == '1':
                s = 'paatos'
            elif s == '2':
                s = 'kasittely'
            if self.verbosity >= 2:
                self.logger.debug('Section: %s' % s)
            section_type = self.SECTION_TYPES[s]
            # sanity check
            subject = section_el.find('SisaltoOtsikko').text
            if subject:
                subject = subject.encode('utf8')
                if subject.replace('ä', 'a').replace('ö', 'o').lower() != s:
                    self.logger.warning("Unexpected section header: %s" % subject)
            text_section = section_el.find('TekstiSektio')
            if not text_section:
                # If it's an empty content section, skip it.
                continue
            paras = self.parse_text_section(text_section)
            content.append((section_type, paras))
        info['content'] = content

    def parse_item_attachments(self, info, item_el):
        att_el_list = item_el.xpath('./LiitteetOptio/Liitteet/LiitteetToisto')
        att_list = []
        for att_el in att_el_list:
            d = {'number': int(att_el.find('Liitenumero').text)}
            id_el = att_el.find('LiitteetId')
            att_list.append(d)
            if id_el == None:
                d['public'] = False
                continue
            else:
                d['public'] = True
            d['id'] = att_el.find('LiitteetId').text
            d['name'] = att_el.find('Liiteteksti').text
            for ext in self.ATTACHMENT_EXTS:
                if d['name'].endswith('.' + ext):
                    d['name'] = d['name'][:-(1+len(ext))]
                    break
        info['attachments'] = att_list

    RESOLUTION_TYPES = {
        1: 'PASSED',
        2: 'PASSED_VOTED',
        3: 'PASSED_REVISED',
        4: 'PASSED_MODIFIED',
        5: 'REJECTED',
        6: 'NOTED',
        7: 'RETURNED',
        8: 'REMOVED',
        9: 'TABLED',
        10: 'ELECTION',
    }

    def parse_desc_el(self, item_el, info):
        desc_el = item_el.find('KuvailutiedotOpenDocument')
        if not desc_el:
            raise ParseError("Field KuvailutiedotOpenDocument missing")
        lang_el = desc_el.find('Kieli')
        if lang_el is not None:
            lang_id = lang_el.attrib['KieliID']
        else:
            # Sometimes the language field can go missing...
            lang_id = 'fi-FI'
        if lang_id != 'fi-FI':
            print "Invalid language: %s" % lang_id
            return False
        register_id_el = desc_el.find('Dnro')
        # If archive id was not found, skip item.
        if not register_id_el:
            return False

        subject = clean_text(desc_el.find('Otsikko').text)
        if subject.startswith('V '):
            # Strip the first word
            subject = subject.split(' ', 1)[1]
            # Strip possible date
            subject = re.sub(r'^\d+\.\d+\.\d+', '', subject)
            # Strip comma and space
            subject = re.sub(r'^[, ]+', '', subject)
        # Strip Kj/Ryj/Kaj...
        subject = re.sub(r'\w{2,4} ?/ *', '', subject)
        info['subject'] = subject

        if self.verbosity >= 2:
            self.logger.debug('Parsing item: %s' % info['subject'])

        info['register_id'] = register_id_el.find('DnroLyhyt').text.strip()
        info['category'] = desc_el.find('Tehtavaluokka').text.strip()

        references = desc_el.find('Viite')
        if references is not None:
            info['reference_text'] = references.text.strip()

        raw_document_classification = desc_el.find('AsiakirjallinenTieto')
        if raw_document_classification is not None:
            m = re.match(r'([0-9 -]+) (\D+)', raw_document_classification.text.strip())
            if m:
                id_no, description = m.groups()
                info['classification_code'] = id_no
                info['classification_description'] = description

        kw_list = []
        for kw_el in desc_el.findall('Asiasanat'):
            kw_list.append(clean_text(kw_el.text))
        info['keywords'] = kw_list

        resolution_el = desc_el.find('Pikapaatos')
        if resolution_el is not None:
            info['resolution'] = self.RESOLUTION_TYPES[int(resolution_el.attrib['PikapaatosId'])]

        introducer_el = desc_el.find('Esittelija')
        if introducer_el is not None:
            info['introducer'] = introducer_el.text.strip()
        preparer_el = desc_el.find('Valmistelija')
        if preparer_el is not None:
            info['preparer'] = preparer_el.text.strip()
        return True

    def parse_item(self, index, item_el, is_top_level=True):
        info = {}
        if self.verbosity >= 3:
            self.logger.debug(etree.tostring(item_el, encoding='utf8', method='html'))

        if is_top_level:
            if not self.parse_desc_el(item_el, info):
                return None

        item_nr = index + 1
        info['number'] = item_nr

        self.parse_item_content(info, item_el)
        self.parse_item_attachments(info, item_el)

        # If we're parsing a minutes entry, find the agenda item entry in order
        # to get better decision text content.
        if is_top_level and self.type == 'minutes':
            agenda_doc_el = item_el.find('Asiakirja')
            if agenda_doc_el:
                ai_content = self.parse_item(index, agenda_doc_el, False)['content']
                for content_type, content in ai_content:
                    if content_type == 'draft resolution':
                        continue
                    # If we don't have the content type already, augment it
                    # with the content from the agenda document.
                    for c in info['content']:
                        if c[0] == content_type:
                            break
                    else:
                        info['content'].append((content_type, content))

        return info

    def parse_from_xml(self, xml_str):
        self.xml_root = etree.fromstring(xml_str)
        if self.xml_root.tag == 'Esityslista':
            self.type = "agenda"
        elif self.xml_root.tag == 'Poytakirja':
            self.type = "minutes"
        else:
            raise ParseError("Invalid root tag in XML file: %s" % self.xml_root.tag)
        self.clean_xml()
        self.parse_header_info()

        if self.type == "minutes":
            item_container = 'Paatokset'
        else:
            item_container = 'Esitykset'
        self.items = []
        item_els = self.xml_root.xpath('./%s/Asiakirja' % item_container)
        for idx, item_el in enumerate(item_els):
            info = self.parse_item(idx, item_el)
            if not info:
                continue
            self.items.append(info)

    def output_cleaned_xml(self, out_file):
        s = etree.tostring(self.xml_root, encoding='utf8')
        out_file.write(s)

    def import_from_zip(self, in_file):
        zipf = zipfile.ZipFile(in_file)
        name_list = zipf.namelist()
        xml_names = [x for x in name_list if x.endswith('.xml')]
        if len(xml_names) == 0:
            # FIXME: Workaround for a silly bug
            xml_names = [x for x in name_list if re.match(r'\w+\d+xml_', x)]
            if len(xml_names) != 1:
                raise ParseError("No XML file in Ahjo ZIP file")
        if len(xml_names) > 1:
            raise ParseError("Too many XML files in Ahjo ZIP file")
        xml_file = zipf.open(xml_names[0])
        xml_s = xml_file.read()
        xml_file.close()
        self.parse_from_xml(xml_s)
        self.zip_file = zipf

    def extract_zip_attachment(self, att, out_path):
        BLOCK_SIZE = 1*1024*1024

        name_list = self.zip_file.namelist()
        names = [x for x in name_list if att['id'] in x]
        if len(names) != 1:
            raise ParseError("Attachment %s not found in ZIP file" % att['id'])
        zip_info = self.zip_file.getinfo(names[0])

        att_file = self.zip_file.open(names[0])
        sha1 = hashlib.new('sha1')
        self.logger.info("Hashing attachment '%s'" % att['name'])
        while True:
            block = att_file.read(BLOCK_SIZE)
            if not block:
                break
            sha1.update(block)
        att['hash'] = sha1.hexdigest()
        att_file.close()

        ext = names[0].split('.')[-1].lower()
        if ext not in self.ATTACHMENT_EXTS:
            # Workaround for an ugly bug
            for e in self.ATTACHMENT_EXTS:
                arr = ext.split('_')
                if len(arr) >= 2 and ext.split('_')[-2].endswith(e):
                    ext = e
                    break

            if ext not in self.ATTACHMENT_EXTS:
                raise ParseError("Unknown attachment type (%s)" % ext)
        att['type'] = ext
        f_name = '%s.%s' % (att['hash'], ext)
        subdir = att['hash'][0:2]
        att['file'] = os.path.join(subdir, f_name)
        storage_dir = os.path.join(out_path, subdir)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        f_path = os.path.join(storage_dir, f_name)
        if os.path.exists(f_path):
            if not self.options.get('ignore-attachment-size', False):
                if os.path.getsize(f_path) != zip_info.file_size:
                    raise ParseError("Size mismatch with attachment '%s': %d vs. %d" % (f_name, os.path.getsize(f_path), zip_info.file_size))
            self.logger.info("Skipping existing attachment '%s'" % f_name)
            return
        self.logger.info("Extracting attachment '%s' to '%s'" % (att['name'], f_name))
        att_file = self.zip_file.open(names[0])
        out_file = open(f_path, 'w')
        while True:
            block = att_file.read(BLOCK_SIZE)
            if not block:
                break
            out_file.write(block)
        out_file.close()
        att_file.close()
