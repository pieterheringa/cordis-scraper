__author__ = 'stefanop'
""" Given the csv file created by `down.py`, builds
 a adjacency matrix of Coordinators and Partners """

import sys
import csv

if len(sys.argv) < 2:
    print "Usage:"
    print "python %s input-file" % sys.argv[0]
    exit(1)

file_in = sys.argv[1]


programmes = {
    'General': ['FP7',
                ],

    'Cooperation': ['FP7-HEALTH',
                    'FP7-COORDINATION',
                    'FP7-ENERGY',
                    'FP7-ENVIRONMENT',
                    'FP7-ICT',
                    'FP7-KBBE',
                    'FP7-NMP',
                    'FP7-SECURITY',
                    'FP7-SPACE',
                    'FP7-SSH',
                    'FP7-TRANSPORT',
                    'FP7-JTI',
                    ],

    'Euratom': ['FP7-EURATOM-FUSION',
                'FP7-EURATOM-FISSION'
                ],

    'Ideas': ['FP7-IDEAS',
              ],

    'Capacities': ['FP7-INCO',
                   'FP7-INFRASTRUCTURES',
                   'FP7-POTENTIAL',
                   'FP7-REGIONAL',
                   'FP7-SIS',
                   'FP7-SME',
                   ],

    'People': ['FP7-PEOPLE',
               ],

    'JRC': []
}

mapping = {}
for programme in programmes:
    for name in programmes[programme]:
        mapping[name] = programme


try:
    fin = open(file_in)
except IOError, e:
    print e
    exit(2)

headers = {}
matrices = {}
for programme in programmes:
    matrices[programme] = ({}, [])

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
            elif cell == 'Theme':
                headers['programme'] = i
        continue

    coordinators, partners = matrices[mapping[cells[headers['programme']]]]

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



for matrix in matrices:
    if len(coordinators) == 0: continue

    file_out = 'matrix_%s.csv' % (matrix)
    fout = open(file_out, 'w')
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
