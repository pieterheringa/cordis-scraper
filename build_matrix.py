""" Given the csv file created by `down.py`, builds
 a adjacency matrix of Coordinators and Partners """
from operator import itemgetter

import os
import sys
import codecs
from clint import args
from clint.textui import puts, indent, progress, colored
from utils import project_ordering_key
from utils.writer import create_txt1, create_txt2
from utils.grouper import group_projects, aggregate
from utils.reader import read_project_file


if len(args.files) != 1:
    print "Usage:"
    print "python %s input-file [options]" % sys.argv[0]
    print "Available options:"
    with indent():
        puts("--aggregate, -a\t\tAggregate output by entities (coordinators and partners)")
        puts("--by-programme, -p\t\tOutput will be grouped by programme")
        puts("--by-year, -y\t\tOutput will be grouped by call year")
        puts("--all\t\t\tBuild all the possible combination of the previous")
    exit(1)


OUT_DIR = 'out/'

AGGREGATE = '-a' in args.flags or '--aggregate' in args.flags
BY_PROGRAMME = '-p' in args.flags or '--by-programme' in args.flags
BY_YEAR = '-y' in args.flags or '--by-year' in args.flags
ALL = '--all' in args.flags
FILE_IN = args.files[0]

if not ALL:
    config = [(AGGREGATE, BY_PROGRAMME, BY_YEAR), ]
else:
    from itertools import product
    config = product([True, False], [True, False], [True, False])

try:
    fin = open(FILE_IN, 'rb')
except Exception, e:
    print e
    exit(2)


# 1. read projects
projects, entity_mapping = read_project_file(fin)


# 2. output entity mapping on RENAMING.txt
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

renaming_out = '%sRENAMING.txt' % (OUT_DIR)
with codecs.open(renaming_out, 'w', encoding='utf-8') as rfout:
    for key, value in sorted(entity_mapping.iteritems(), key=lambda x: project_ordering_key(x[1])):
        rfout.write(u"{1}\t\t{0}\r\n".format(key, entity_mapping[key]))


# 3. for each configuration required, output the matrices
for AGGREGATE, BY_PROGRAMME, BY_YEAR in config:
    print
    print colored.green("Running with aggregate={0} by-programme={1} by-year={2}".format(
        AGGREGATE, BY_PROGRAMME, BY_YEAR))
    matrices = group_projects(projects, by_programme=BY_PROGRAMME, by_year=BY_YEAR)

    print "Writing output matrices"
    for theme, matrix in progress.bar(matrices.iteritems(), expected_size=len(matrices)):
        if not len(matrix):
            continue

        if AGGREGATE:
            file_out = '{0}matrix_network_{1}.txt'.format(OUT_DIR, theme)

            aggreg_matrix = aggregate(matrix)

            with codecs.open(file_out, 'w', encoding='utf-8') as fout:
                create_txt1(fout, aggreg_matrix)
        else:
            file_out = '{0}matrix_calls_{1}.txt'.format(OUT_DIR, theme)

            with codecs.open(file_out, 'w', encoding='utf-8') as fout:
                create_txt2(fout, matrix)
