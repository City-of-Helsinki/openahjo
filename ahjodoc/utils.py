import tempfile
import requests
import shutil
from progressbar import ProgressBar

CHUNK_SIZE = 32*1024

def download_file(url, output_fname=None):
    outf = tempfile.NamedTemporaryFile(mode="w+b", delete=True)

    resp = requests.get(url, stream=True)
    total_len = int(resp.headers['content-length'])
    if total_len > 1*1024*1024:
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
    if output_fname:
        outf.delete = False
        outf.close()
        shutil.move(outf.name, output_fname)
        outf = open(output_fname, 'rb')
    else:
        outf.seek(0)
    return outf
