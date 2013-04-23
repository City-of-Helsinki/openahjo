#!/usr/bin/env python
import os
import tempfile
import shutil
import requests
import requests_cache
import logging
from datetime import datetime
from lxml import html
from progressbar import ProgressBar
from .doc import local_timezone

CHUNK_SIZE = 32*1024

URL_BASE = "http://openhelsinki.hel.fi"

class AhjoScanner(object):
    def __init__(self):
        self.doc_store_path = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def scan_dir(self, path, committee_id):
        r = requests.get(URL_BASE + path)
        if r.status_code != 200:
            raise Exception("Failed to read directory '%s'" % path)
        root = html.fromstring(r.content)
        links = root.xpath("//a")
        info_list = []
        for link_el in links:
            link = link_el.attrib['href']
            if not link.endswith('.zip'):
                continue
            fname = link.split('/')[-1]
            fname = fname.replace('.zip', '')
            FIELD_NAMES = ("org", "date", "committee", "meeting_nr", "doc_type_id", "language")
            fields = fname.split('%20')
            info = {}
            if len(fields) == len(FIELD_NAMES) - 1:
                self.logger.warning("Language field missing in %s" % ' '.join(fields))
                fields.append('Su')
            for idx, f in enumerate(FIELD_NAMES):
                info[f] = fields[idx]
            info['meeting_nr'] = int(info['meeting_nr'])
            info['committee_id'] = committee_id
            # Skip Swedish documents
            if info['language'] != 'Su':
                continue

            DOC_TYPES = {'Pk': 'minutes', 'El': 'agenda'}
            info['doc_type'] = DOC_TYPES[info['doc_type_id']]

            # Fetch timestamp from directory listing
            ts_text = link_el.getprevious().tail.split('    ')[0].strip()
            time = datetime.strptime(ts_text, "%m/%d/%Y %I:%M %p")
            time = time.replace(tzinfo=local_timezone)
            info['last_modified'] = time

            info['url'] = URL_BASE + link
            info['origin_id'] = self.generate_doc_id(info)
            info_list.append(info)
        return info_list

    def scan_documents(self, cached=False):
        if cached:
            requests_cache.install_cache()
        r = requests.get(URL_BASE + '/files/')
        if r.status_code != 200:
            raise Exception("Directory read failed")
        root = html.fromstring(r.content)
        links = root.xpath("//a")
        info_list = []
        for link_el in links:
            link = link_el.attrib['href']
            if not link.startswith('/files'):
                continue
            committee_id = link_el.text.split('_')[-1].strip()
            dir_list = self.scan_dir(link, committee_id)
            info_list = info_list + dir_list
        self.doc_list = info_list
        if cached:
            requests_cache.uninstall_cache()
        return info_list

    def generate_doc_id(self, info):
        s = "%s_%s_%d_%s" % (info['org'], info['committee'], info['meeting_nr'], info['doc_type_id'])
        return s

    def download_document(self, info):
        self.logger.info('Fetching document from %s' % info['url'])

        if self.doc_store_path:
            try:
                os.makedirs(self.doc_store_path)
            except OSError:
                pass
            fname = "%s_%s.zip" % (info['date'], self.generate_doc_id(info))
            store_fpath = os.path.join(self.doc_store_path, fname)
            if os.path.exists(store_fpath):
                return open(store_fpath, 'rb')
            delete_tmp = False
        else:
            store_fpath = None
            delete_tmp = True

        outf = tempfile.NamedTemporaryFile(mode="w+b", delete=delete_tmp)

        resp = requests.get(info['url'], stream=True)
        total_len = int(resp.headers['content-length'])
        pbar = ProgressBar(maxval=total_len).start()
        bytes_down = 0
        for chunk in resp.iter_content(CHUNK_SIZE):
            outf.write(chunk)
            bytes_down += len(chunk)
            pbar.update(bytes_down)
        pbar.finish()
        if store_fpath:
            outf.close()
            shutil.move(outf.name, store_fpath)
            outf = open(store_fpath, 'rb')
        else:
            outf.seek(0)
        return outf

if __name__ == "__main__":
    scanner = AhjoScanner()
    logging.basicConfig()
    scanner.doc_store_path = ".cache"

    doc_list = scanner.scan_documents()

    for doc in doc_list:
        scanner.download_document(doc)
