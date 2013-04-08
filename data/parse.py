#!/usr/bin/env python
import re
import csv

f = open('category-map-from-pdf.txt', 'r')

outf = open('categories.csv', 'w')
writer = csv.writer(outf)

def clean_text(text):
    text = text.replace('\n', ' ')
    # remove consecutive whitespaces
    return re.sub(r'\s\s+', ' ', text, re.U).strip()

def output_entry(code, name):
    code = clean_text(code.decode('utf8'))
    name = name.decode('utf8')
    if len(code) == 2:
        name = name[0:1].upper() + name[1:].lower()
    name = name.encode('utf8')
    code = code.encode('utf8')
    print "%-10s\t%s" % (code, name)
    writer.writerow((code, name))

state = "code"
for line in f.readlines():
    line = line.strip()
    if not line:
        continue
    if state == "code":
        m = re.match(r"(\d\d[\s]*)+", line)
        if not m:
            continue
        code = line[0:m.end()].strip()
        rest = line[m.end():].strip()
        if rest:
            if rest[-1] in ('-',):
                state = "multiline"
                continue
            else:
                output_entry(code, rest)
        else:
            state = "name"
    elif state == "name":
        if line[-1] in ('-',):
            rest = line
            state = "multiline"
            continue
        output_entry(code, line)
        state = "code"
    elif state == "multiline":
        output_entry(code, rest[0:-1] + line)
        state = "code"
