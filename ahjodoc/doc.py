# -*- coding: utf-8 -*-
import re
from lxml import etree, html, objectify
import zipfile
import logging
from pytz import timezone
from datetime import datetime

local_timezone = timezone('Europe/Helsinki')

class ParseError(Exception):
    pass

def clean_text(text):
    text = text.replace('\n', ' ')
    # remove consecutive whitespaces
    return re.sub(r'\s\s+', ' ', text, re.U).strip()

class AhjoDocument(object):
    def __init__(self):
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
        date = desc_info.find('JulkaisuEsilletulopaiva').text
        time = desc_info.find('JulkaisuEsilletuloklo').text
        time_str = "%s %s" % (date, time)
        self.publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        self.publish_time.replace(tzinfo=local_timezone)

        committee_el = self.xml_root.xpath('./YlatunnisteSektio/Paattaja')[0]
        self.committee_id = committee_el.attrib['PaattajaId']

    def parse_text_section(self, section_el):
        children = section_el.getchildren()
        content = []
        for ch in children:
            if ch.tag != 'taso1':
                raise ParseError("Unexpected text section container: %s" % ch.tag)
            paras = ch.getchildren()
            for p in paras:
                if p.tag not in ('Kappale', 'Otsikko', 'Henkilotietoa', 'XHTML', 'Kuva'):
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
                    content.append(u'<h3>%s</h3>' % clean_text(p.text))
                elif p.tag == 'Henkilotietoa':
                    content.append(u'<span class="redacted-personal-information">*****</span>')
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
        'tiivistelma': 'summary',
        'esittelija': 'presenter',
        'paatos': 'resolution',
        'kasittely': 'hearing',
    }
    def parse_item_content(self, info, item_el):
        section_el_list = item_el.xpath('./SisaltoSektioToisto/SisaltoSektio')
        content = []
        for section_el in section_el_list:
            if 'sisaltosektioTyyppi' in section_el.attrib:
                s = section_el.attrib['sisaltosektioTyyppi']
            else:
                self.logger.warning("attribute sisaltosektioTyyppi not found")
                s = section_el.find('SisaltoOtsikko').attrib['SisaltoOtsikkoTyyppi']
            if s == '1':
                s = 'paatos'
            elif s == '2':
                s = 'kasittely'
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

    def parse_item(self, index, item_el):
        info = {}
        desc_el = item_el.find('KuvailutiedotOpenDocument')
        lang_id = desc_el.find('Kieli').attrib['KieliID']
        if lang_id != 'fi-FI':
            print "Invalid language: %s" % lang_id
            return
        register_id_el = desc_el.find('Dnro')
        # If archive id was not found, skip item.
        if not register_id_el:
            return

        info['subject'] = desc_el.find('Otsikko').text.strip()
        if self.type == 'minutes':
            item_nr = int(desc_el.find('Pykala').text)
        else:
            item_nr = index
        info['register_id'] = register_id_el.find('DnroLyhyt').text.strip()
        info['number'] = item_nr
        info['category'] = desc_el.find('Tehtavaluokka').text.strip()
        self.parse_item_content(info, item_el)
        self.items.append(info)

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
            self.parse_item(idx, item_el)

    def output_cleaned_xml(self, out_file):
        s = etree.tostring(self.xml_root, encoding='utf8')
        out_file.write(s)

    def import_from_zip(self, in_file):
        zipf = zipfile.ZipFile(in_file)
        name_list = zipf.namelist()
        xml_names = [x for x in name_list if x.endswith('.xml')]
        if len(xml_names) != 1:
            raise ParseError("Too many XML files in Ahjo ZIP file")
        xml_file = zipf.open(xml_names[0])
        xml_s = xml_file.read()
        xml_file.close()
        self.parse_from_xml(xml_s)
