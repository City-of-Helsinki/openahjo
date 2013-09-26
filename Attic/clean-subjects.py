import re
from ahjodoc.models import *

def clean_text(text):
    import re
    text = text.replace('\n', ' ')
    # remove consecutive whitespaces
    return re.sub(r'\s\s+', ' ', text, re.U).strip()

def clean_subject(subject):
    import re
    if subject.startswith('V '):
        # Strip the first word
        subject = subject.split(' ', 1)[1]
        # Strip possible date
        subject = re.sub(r'^\d+\.\d+\.\d+', '', subject)
        # Strip comma and space
        subject = re.sub(r'^[, ]+', '', subject)
    # Strip Kj/Ryj/Kaj...
    subject = re.sub(r'^\w{2,4} ?/ *', '', subject)
    return subject

ai_list = AgendaItem.objects.filter(meeting__policymaker__origin_id__in=['00400', '02900'])
for ai in ai_list:
    s = clean_text(clean_subject(ai.subject))
    if s != ai.subject:
        print "  %s" % ai.subject.encode('utf8')
        print "->%s" % s.encode('utf8')
        ai.subject = s
        ai.save()

ai_list = AgendaItem.objects.filter(subject__contains='  ')
for ai in ai_list:
    ai.subject = clean_text(ai.subject)
    ai.save()

issue_list = Issue.objects.all()
for i in issue_list:
    s = i.determine_subject()
    if s != i.subject:
        print "  %s" % i.subject.encode('utf8')
        print "->%s" % s.encode('utf8')
        i.subject = s
        i.save()

