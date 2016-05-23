#!/usr/bin/env python
import sys
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

SKIP_DOC_LIST = [
    'Opev_SKJ_2013-2_El',
    'HKR_Ytlk_2013-18_El',
    'Ymk_Ylk_2013-1_El',
    'Ork_Orkjk_2014-4_Pk', # HEL 2014-011315 processed twice
    'Rakpa_Tplk_2013-1_Pk', # KuvailutiedotOpenDocument missing
    'Halke_Khs_2012-27_Pk', # Attachment missing
    'Halke_Khs_2012-26_Pk', # Attachment missing
]

SKIP_URL_LIST = [
    'http://openhelsinki.hel.fi/files/Taloushallintopalvelu-liikelaitoksen%20jk_71900/Talpa%202013-05-28%20Talpajk%203%20El%20Su.zip', # Duplicate
    'http://openhelsinki.hel.fi/files/Kaupunginhallituksen%20konsernijaosto_02978/Halke%202013-08-26%20Koja%2011%20El%20Su.zip', # Wrong meeting id
    'http://openhelsinki.hel.fi/files/Kaupunginhallituksen%20konsernijaosto_02978/Halke%202013-08-26%20Koja%2011%20Pk%20Su.zip', # Wrong meeting id
    'http://openhelsinki.hel.fi/files/Kaupunginmuseon%20johtokunta_46113/Museo%202013-08-27%20Museojk%207%20El%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Kaupunginmuseon%20johtokunta_46113/Museo%202013-08-27%20Museojk%207%20Pk%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Suomenkielisen%20tyovaenopiston%20jk_45100/Sto%202013-08-27%20Stojk%2012%20El%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Suomenkielisen%20tyovaenopiston%20jk_45100/Sto%202013-08-27%20Stojk%2012%20Pk%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Taloushallintopalvelu-liikelaitoksen%20jk_71900/Talpa%202013-11-26%20Talpajk%205%20El%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Keskusvaalilautakunta_11500/Kanslia%202014-09-02%20Kvlk%207%20El%20Su.zip', # wrong date
    'http://openhelsinki.hel.fi/files/Liikuntalautakunta_47100/Liv%202014-10-23%20LILK%2012%20El%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Pelastuslautakunta_11100/Pel%202014-06-10%20PELK%207%20El%20Su.zip', # corrupt
    'http://openhelsinki.hel.fi/files/Liikuntalautakunta_47100/Liv%202014-10-23%20LILK%2011%20El%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Liikuntalautakunta_47100/Liv%202014-10-07%20LILK%2015%20El%20Su.zip', # wrong meeting id
    'http://openhelsinki.hel.fi/files/Taidemuseo_46102/Museonjohtaja_46102VH1/Taimu%202104-10-10%2046102VH1%2026%20Pk%20Su.zip', # wrong date
    'http://openhelsinki.hel.fi/files/Rakennusvirasto_52000/Tulosryhman%20johtaja_521112VH1/HKR%202014-12-16%20521112VH1%2012%20Pk%20Su.zip', # wrong date
    'http://openhelsinki.hel.fi/files/Sosiaali-%20ja%20terveyslautakunta_81000/Sote%202013-06-04%20Sotelk%209%20Pk%20Su.zip', # missing attachment
    'http://openhelsinki.hel.fi/files/Sosiaali-%20ja%20terveyslautakunta_81000/Sote%202013-06-04%20Sotelk%209%20El%20Su.zip', # missing attachment
]

CHUNK_SIZE = 32*1024

URL_BASE = "http://openhelsinki.hel.fi"

class AhjoScanner(object):
    def __init__(self, verbosity=1):
        self.verbosity = verbosity
        self.doc_store_path = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def scan_dir(self, path, policymaker_id):
        r = requests.get(URL_BASE + path)
        if r.status_code != 200:
            raise Exception("Failed to read directory '%s'" % path)
        root = html.fromstring(r.content)
        links = root.xpath("//a")
        info_list = []
        for link_el in links:
            link = link_el.attrib['href']
            if path in link and link.endswith('/'):
                # Is a sub-directory
                new_policymaker_id = link.strip('/').split('_')[-1].strip()
                sub_list = self.scan_dir(link, new_policymaker_id)
                info_list += sub_list
                continue

            if not link.endswith('.zip'):
                continue

            fname = link.split('/')[-1]
            fname = fname.replace('.zip', '')
            FIELD_NAMES = ("org", "date", "policymaker", "meeting_nr", "doc_type_id", "language")
            fields = fname.split('%20')
            info = {}
            if len(fields) == len(FIELD_NAMES) - 1:
                self.logger.warning("Language field missing in %s" % ' '.join(fields))
                fields.append('Su')
            for idx, f in enumerate(FIELD_NAMES):
                info[f] = fields[idx]
            info['meeting_nr'] = int(info['meeting_nr'])
            info['year'] = int(info['date'].split('-')[0])
            info['policymaker_id'] = policymaker_id
            info['policymaker_abbr'] = info['policymaker']
            # Skip Swedish documents
            if info['language'] != 'Su':
                continue

            DOC_TYPES = {'Pk': 'minutes', 'El': 'agenda'}
            info['doc_type'] = DOC_TYPES[info['doc_type_id']]

            # Fetch timestamp from directory listing
            elems = link_el.getprevious().tail.split('   ')
            ts_text = elems[0].strip()
            file_size = int(elems[-1].strip())
            time = datetime.strptime(ts_text, "%m/%d/%Y %I:%M %p")
            time = time.replace(tzinfo=local_timezone)
            info['last_modified'] = time

            info['url'] = URL_BASE + link
            if file_size < 500:
                self.logger.warning("File too small: %s %d" % ((URL_BASE + link), file_size))
                continue
            info['origin_id'] = self.generate_doc_id(info)
            if info['url'] in SKIP_URL_LIST:
                self.logger.warning("Skipping document on URL skip list: %s" % info['origin_id'])
                continue
            if info['origin_id'] in SKIP_DOC_LIST:
                self.logger.warning("Skipping document on skip list: %s" % info['origin_id'])
                continue

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
            policymaker_id = link_el.text.split('_')[-1].strip()
            dir_list = self.scan_dir(link, policymaker_id)
            info_list = info_list + dir_list
        self.doc_list = info_list
        if cached:
            requests_cache.uninstall_cache()
        return info_list

    def generate_doc_id(self, info):
        s = "%s_%s_%d-%d_%s" % (info['org'], info['policymaker'], info['year'], info['meeting_nr'], info['doc_type_id'])
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
                mtime = datetime.fromtimestamp(os.path.getmtime(store_fpath))
                mtime = mtime.replace(tzinfo=local_timezone)
                # Use stored file only if it's newer.
                if mtime >= info['last_modified']:
                    return open(store_fpath, 'rb')
            delete_tmp = False
        else:
            store_fpath = None
            delete_tmp = True

        outf = tempfile.NamedTemporaryFile(mode="w+b", delete=delete_tmp)

        resp = requests.get(info['url'], stream=True)
        total_len = int(resp.headers['content-length'])
        if sys.stdout.isatty():
            pbar = ProgressBar(maxval=total_len).start()
        else:
            pbar = None
        bytes_down = 0
        for chunk in resp.iter_content(CHUNK_SIZE):
            outf.write(chunk)
            bytes_down += len(chunk)
            if pbar:
                pbar.update(bytes_down)
        if pbar:
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
