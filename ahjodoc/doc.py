# -*- coding: utf-8 -*-
from lxml import etree
import zipfile
import logging
from pytz import timezone
from datetime import datetime

local_timezone = timezone('Europe/Helsinki')

class AhjoDocument(object):
    def __init__(self):
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

    def parse_from_xml(self, xml_str):
        self.xml_root = etree.fromstring(xml_str)
        if self.xml_root.tag == 'Esityslista':
            self.type = "agenda"
        elif self.xml_root.tag == 'Poytakirja':
            self.type = "minutes"
        else:
            raise Exception("Invalid root tag in XML file: %s" % self.xml_root.tag)
        self.clean_xml()
        self.parse_header_info()

    def output_cleaned_xml(self, out_file):
        s = etree.tostring(self.xml_root, encoding='utf8')
        out_file.write(s)

    def import_from_zip(self, in_file):
        zipf = zipfile.ZipFile(in_file)
        name_list = zipf.namelist()
        xml_names = [x for x in name_list if x.endswith('.xml')]
        if len(xml_names) != 1:
            raise Exception("Too many XML files in Ahjo ZIP file")
        xml_file = zipf.open(xml_names[0])
        xml_s = xml_file.read()
        xml_file.close()
        self.parse_from_xml(xml_s)

if __name__ == "__main__":
    from scanner import AhjoScanner

    scanner = AhjoScanner()
    scanner.doc_store_path = ".cache"
    logging.basicConfig()
    doc_list = scanner.scan_documents()
    doc_f = scanner.download_document(doc_list[0])
    doc = AhjoDocument()
    doc.import_from_zip(doc_f)
