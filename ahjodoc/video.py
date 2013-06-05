import re
import json
import requests

from doc import ParseError
from ffvideo import VideoStream
#from models import Meeting, Issue, AgendaItem

INDEX_URL = "http://www.helsinkikanava.fi/@@opendata-index-v2.0"

cached_meetings = None

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
        m = re.match(u'[\w ]+(\d+)/(\d{1,2}\.\d{1,2}.\d{4})', sess['title'])
        if not m:
            continue
        meeting_nr = int(m.groups()[0])
        meeting_date = '-'.join(reversed(m.groups()[1].split('.')))
        year = meeting_date.split('-')[0]
        url = sess['url']
        #url = url.split('@@')[0]
        #url += '@@hallinfo-meeting'
        meetings.append({'url': url, 'nr': meeting_nr, 'date': meeting_date, 'year': int(year)})

    cached_meetings = meetings
    return meetings

cached_meeting_entries = {}

def fetch_meeting(meeting):
    meet_id = '%s/%s' % (meeting['nr'], meeting['year'])
    if meet_id in cached_meeting_entries:
        return cached_meeting_entries[meet_id]

    r = requests.get(meeting['url'])
    ret = r.json()
    cached_meeting_entries[meet_id] = ret
    return ret

def get_videos_for_meeting(meeting):
    meetings = fetch_meetings()
    for m in meetings:
        if m['year'] == meeting['year'] and m['nr'] == meeting['nr']:
            return fetch_meeting(m)
    return None

def open_video(url):
    return VideoStream(url)
    
def get_video_frame(video, pos):
    return video.get_frame_at_sec(pos).image()
