import re
import json
import requests
import subprocess
import datetime

from doc import ParseError

INDEX_URL = "http://www.helsinkikanava.fi/@@opendata-index-v2.0"

cached_meetings = None

def fix_meeting_quirks(meeting):
    if meeting['title'] == 'Kaupunginvaltuuston kokous 19/14.11.2012':
        issues = meeting['issues']
        issues[2]['id'] = '3'
        issues[3]['id'] = '4'
        issues[4]['id'] = '5'
    return meeting

def fetch_meetings():
    global cached_meetings

    if cached_meetings:
        return cached_meetings
    r = requests.get(INDEX_URL)
    ret = r.json()
    sess_list = ret['sessions']
    meetings = []
    for sess in sess_list:
        if 'Kaupunginvaltuuston' not in sess['title']:
            continue
        m = re.match(u'[\w ]+ (\d+)/(\d{1,2}\.\d{1,2}.\d{4})', sess['title'])
        if not m:
            continue
        meeting_nr = int(m.groups()[0])
        meeting_date = '-'.join(reversed(m.groups()[1].split('.')))
        year = meeting_date.split('-')[0]
        url = sess['url']
        #url = url.split('@@')[0]
        #url += '@@hallinfo-meeting'
        meeting = {'url': url, 'nr': meeting_nr, 'date': meeting_date, 'year': int(year)}
        meetings.append(meeting)
    cached_meetings = meetings
    return meetings

cached_meeting_entries = {}

def fetch_meeting(meeting):
    meet_id = '%s/%s' % (meeting['nr'], meeting['year'])
    if meet_id in cached_meeting_entries:
        return cached_meeting_entries[meet_id]

    r = requests.get(meeting['url'])
    ret = r.json()
    fix_meeting_quirks(ret)
    cached_meeting_entries[meet_id] = ret
    return ret

def get_videos_for_meeting(meeting):
    meetings = fetch_meetings()
    for m in meetings:
        if m['year'] == meeting['year'] and m['nr'] == meeting['nr']:
            return fetch_meeting(m)
    return None


class VideoFile(object):
    def __init__(self, fpath):
        self.video_path = fpath

    def get_duration(self):
        args = ['avprobe', '-show_format', '-of', 'json', self.video_path]
        result = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result.wait()
        if result.returncode != 0:
            raise Exception("avprobe invocation failed (cmd: %s)" % ' '.join(args))
        json_str = ''.join(result.stdout.readlines())
        d = json.loads(json_str)
        duration = int(float(d['format']['duration']))
        return duration

    def take_screenshot(self, pos, out_fname):
        time_str = str(datetime.timedelta(seconds=pos))
        args = ['ffmpegthumbnailer', '-i', self.video_path, '-s0', '-t', time_str, '-o', out_fname]
        result = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result.wait()
        if result.returncode != 0:
            raise Exception("ffmpegthumbnailer invocation failed (cmd: %s)" % ' '.join(args))
