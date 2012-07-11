# -*- coding: utf-8 -*-
""" utility functions for reading the project CSV file
"""
import csv


def _build_headers(cells):
    """ given a list of cells containing labels, return a mapping of type
    cell_id -> label useful for building objects
    """
    return [cell if not cell.find('Partner') == 0 else 'partners'
            for cell in cells]


def _build_project(cells, headers):
    """ given a list of cells and a list of headers, return a dictionary
    mapping headers to cell contents.
    """
    project = {}
    for key, value in zip(headers, cells):
        if key == 'partners':
            if key not in project:
                project[key] = []
            project[key].append(value)
        else:
            project[key] = value
    project['partners'] = [x for x in project['partners'] if x]
    return project


def _convert_to_right_type(a_dict):
    """ tries to convert the values of a dictionary to int or date
    """
    from time import strptime, mktime
    from datetime import date

    for key in a_dict:
        if not isinstance(a_dict[key], (unicode, str)):
            continue

        try:
            a_dict[key] = int(a_dict[key])
        except ValueError:
            try:
                struct_time = strptime(a_dict[key], "%Y-%m-%d")
                a_dict[key] = date.fromtimestamp(mktime(struct_time))
            except ValueError:
                pass


UMLAUT = u'\u0308'
def strip_accents(s):
    import unicodedata
    return ''.join((
        'e' if c == UMLAUT else c
        for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn' or c == UMLAUT
    ))


def trucate_country(s):
    import re
    return re.sub(' - country: [\w]*', lambda x: x.group()[:11], s)


def _adjust_name(name):
    """ clean a name for matching
    """
    return trucate_country(strip_accents(
            name.lower().replace(u'ë', u'e')
                        .replace(u'ï', u'i')
                        .replace(u"'", u'')
                        .replace(u",", u'')
                        .replace(u".", u'')
                        .replace(u"'", u'')
                        .replace(u"'", u'')
        )
    )


def _map_entities(project, entity_codes, entity_mapping):
    """ replace Coordinator and partners with a code, and write the mapping
    in the entity_mapping
    """
    def _f(name):
        key = _adjust_name(name)
        if key not in entity_codes:
            entity_codes[key] = u'N_{0}'.format(len(entity_mapping))
        if name not in entity_mapping:
            entity_mapping[name] = entity_codes[key]
        return entity_mapping[name]

    project['Coordinator'] = _f(project['Coordinator'])
    for i, partner in enumerate(project.get('partners', [])):
        project['partners'][i] = _f(project['partners'][i])


def _unicode_csv_reader(csv_data, dialect=csv.excel, **kwargs):
    """ adapted from http://docs.python.org/library/csv.html#csv-examples
    """
    csv_reader = csv.reader(csv_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def read_project_file(fin):
    from clint.textui import progress
    print "Reading projects"

    total = len(fin.readlines())
    fin.seek(0)

    headers = None
    projects = []
    entity_mapping = {}
    entity_codes = {}
    csv_reader = _unicode_csv_reader(fin, delimiter=',', quotechar='"')
    for cells in progress.bar(csv_reader, expected_size=total):
        if not headers:
            headers = _build_headers(cells)
            continue
        else:
            project = _build_project(cells, headers)
            _convert_to_right_type(project)
            _map_entities(project, entity_codes, entity_mapping)

            projects.append(project)

    print "Read {0} projects".format(len(projects))
    return projects, entity_mapping
