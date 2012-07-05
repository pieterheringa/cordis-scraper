""" Given the csv file created by `down.py`, builds
 a adjacency matrix of Coordinators and Partners """
__author__ = 'stefanop'

import os
import csv
import sys
from utils import create_csv, create_net, create_txt1, create_txt2

if len(sys.argv) < 3:
    print "Usage:"
    print "python %s input-file <csv|net|1.txt|2.txt>" % sys.argv[0]
    exit(1)

file_in = sys.argv[1]
out_format = sys.argv[2]

assert(out_format in ("csv", "net", "1.txt", "2.txt"))

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

AGGREGATE = True if out_format != "2.txt" else False
SUB_MATRICES = True
ENABLED = ['Cooperation', 'Capacities']
OUT_DIR = 'out/'

mapping = {}
for programme in programmes:
    for name in programmes[programme]:
        if programme in ENABLED or '*' in ENABLED:
            mapping[name] = programme if not SUB_MATRICES else name

try:
    fin = open(file_in)
except IOError, e:
    print e
    exit(2)

headers = {}
matrices = {}
for key in mapping:
    matrices[mapping[key]] = ({}, []) if AGGREGATE else {}

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
            elif cell == 'Activities (research area)':
                headers['activities'] = i
        continue

    programme = cells[headers['programme']]
    if not programme in mapping:
        continue

    if AGGREGATE:
        coordinators, partners = matrices[mapping[programme]]

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
    else:
        calls = matrices[mapping[programme]]
        
        activities = cells[headers['activities']]
        if activities not in calls:
            calls[activities] = []
        coordinator = cells[headers['coordinator']]
        partners = []
        for column in headers['partners']:
            partner = cells[column]
            if not partner:
                continue
            partners.append(partner)
        calls[activities].append((coordinator, partners))


for matrix in matrices:
    if AGGREGATE:
        coordinators, partners = matrices[matrix]
        if len(coordinators) == 0: continue
    else:
        calls = matrices[matrix]
        if len(calls) == 0: continue

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    file_out = '%smatrix_%s.%s' % (OUT_DIR, matrix, out_format)
    renaming_out = 'matrix_%s_renaming.txt' % matrix
    fout = open(file_out, 'w')
    rfout = open(renaming_out, 'w')

    if out_format == 'csv':
        create_csv(fout, coordinators, partners)
    elif out_format == 'net':
        create_net(fout, coordinators, partners)
    elif out_format == '1.txt':
        create_txt1(fout, coordinators, partners, rfout)
    elif out_format == '2.txt':
        create_txt2(fout, calls)

    rfout.close()
    fout.close()
