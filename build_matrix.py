__author__ = 'stefanop'
""" Given the csv file created by `down.py`, builds
 a adjacency matrix of Coordinators and Partners """

import sys
import csv

if len(sys.argv) < 3:
    print "Usage:"
    print "python %s input-file output-file" % sys.argv[0]
    exit(1)

file_in = sys.argv[1]
file_out = sys.argv[2]

try:
    fin = open(file_in)
    fout = open(file_out, 'w')
except IOError, e:
    print e
    exit(2)

headers = {}
coordinators = {}
partners = []
csv_reader = csv.reader(fin, delimiter=',', quotechar='"')
for cells in csv_reader:
    if len(headers) == 0:
        for i, cell in enumerate(cells):
            if cell == 'Coordinator':
                headers['coordinator'] = i
            elif cell.find('Partner') == 0:
                if 'partners' not in headers:
                    headers['partners'] = []
                headers['partners'].append(i)
        continue

    coordinator = cells[headers['coordinator']]
    if coordinator not in coordinators:
        coordinators[coordinator] = {}

    for column in headers['partners']:
        partner = cells[column]
        if not partner:
            continue
        if partner not in partners:
            partners.append(partner)
        if partner not in coordinators[coordinator]:
            coordinators[coordinator][partner] = 0
        coordinators[coordinator][partner] += 1


csv_writer = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
csv_writer.writerow([''] + partners)

for coordinator in coordinators:
    row = [coordinator]
    for partner in partners:
        value = 0
        if partner in coordinators[coordinator]:
            value = coordinators[coordinator][partner]
        row.append(unicode(value))
    csv_writer.writerow(row)
