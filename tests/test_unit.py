# -*- coding: utf-8 -*-
import unittest
from utils import project_ordering_key
from utils.reader import read_project_file, _build_headers, _build_project,\
    _convert_to_right_type, _adjust_name


class TestUtilsInit(unittest.TestCase):
    def test_project_ordering_key(self):
        keys = ['N_1', 'N_20341', '']
        results = {key: set() for key in keys}

        for _ in range(100):
            for key in keys:
                results[key].add(project_ordering_key(key))

        for result in results.values():
            self.assertEqual(len(result), 1)


class TestUtilsReader(unittest.TestCase):
    def test_read_project_file(self):
        with open('tests/projects.test.csv') as fin:
            projects, entity_mapping = read_project_file(fin)
            self.assertEqual(len(projects), 6)
            self.assertEqual(len(entity_mapping), 7)

            self.assertEqual(projects[0]['Coordinator'], entity_mapping['Coord one'])
            self.assertEqual(len(projects[0]['partners']), 1)
            self.assertEqual(projects[0]['partners'][0], entity_mapping['Par 1'])

            self.assertEqual(projects[1]['Coordinator'], entity_mapping['Coord two'])
            self.assertEqual(len(projects[1]['partners']), 1)
            self.assertEqual(projects[1]['partners'][0], entity_mapping['Part 2'])

            self.assertEqual(projects[2]['Coordinator'], entity_mapping['Coord two'])
            self.assertEqual(len(projects[2]['partners']), 1)
            self.assertEqual(projects[2]['partners'][0], entity_mapping['Par 1'])

            self.assertEqual(projects[3]['Coordinator'], entity_mapping['Coord three'])
            self.assertEqual(len(projects[3]['partners']), 2)
            self.assertEqual(projects[3]['partners'][0], entity_mapping['Part 2'])
            self.assertEqual(projects[3]['partners'][1], entity_mapping['Par 1'])

            self.assertEqual(projects[4]['Coordinator'], entity_mapping['Coo'])
            self.assertEqual(len(projects[4]['partners']), 3)
            self.assertEqual(projects[4]['partners'][0], entity_mapping['Par 1'])
            self.assertEqual(projects[4]['partners'][1], entity_mapping['Par 3'])
            self.assertEqual(projects[4]['partners'][2], entity_mapping['Part 2'])

            self.assertEqual(projects[5]['Coordinator'], entity_mapping['Coord one'])
            self.assertEqual(len(projects[5]['partners']), 1)
            self.assertEqual(projects[5]['partners'][0], entity_mapping['Par 1'])

    def test_build_headers(self):
        cells = ['something', 'something else', 'Partner 1', 'Partner 2']
        headers = _build_headers(cells)
        self.assertEqual(headers, ['something', 'something else', 'partners', 'partners'])

    def test_build_project(self):
        cells = ['12', 'something', '2011-12-12', 'something a', 'something b']
        headers = ['something', 'something else', 'a date', 'partners', 'partners']
        project = _build_project(cells, headers)

        self.assertEqual(project['something'], '12')
        self.assertEqual(project['something else'], 'something')
        self.assertEqual(project['a date'], '2011-12-12')
        self.assertEqual(project['partners'], ['something a', 'something b'])

    def test_convert_to_right_type(self):
        from datetime import date
        a_dict = {
            'a number': '2314',
            'a date': '2011-12-31',
            'a list': ['something', 'something'],
            'a string': 'foo',
        }
        _convert_to_right_type(a_dict)
        self.assertIsInstance(a_dict['a number'], int)
        self.assertIsInstance(a_dict['a date'], date)
        self.assertIsInstance(a_dict['a list'], list)
        self.assertIsInstance(a_dict['a string'], str)
        self.assertEqual(a_dict['a number'], 2314)
        self.assertEqual(a_dict['a string'], 'foo')

    def test_map_entities(self):
        pass

    def test_adjust_name(self):
        self.assertEqual(
            _adjust_name(u'Università degli studi di Trento'),
            _adjust_name(u'Universita degli studi di Trento'),
        )
        self.assertEqual(
            _adjust_name(u'Österreich'),
            _adjust_name(u'Oesterreich'),
        )
        self.assertEqual(
            _adjust_name(u'België'),
            _adjust_name(u'Belgie'),
        )
        self.assertEqual(
            _adjust_name(u'UNIVERSIDAD POLITECNICA DE MADRID - COUNTRY: ESPAÑA'),
            _adjust_name(u'UNIVERSIDAD POLITECNICA DE MADRID - COUNTRY: ES'),
        )
        self.assertEqual(
            _adjust_name(u"Universita' di Trieste"),
            _adjust_name(u'Universita di Trieste'),
        )
        self.assertEqual(
            _adjust_name(u"UNIVERSITA DEGLI STUDI DI NAPOLI FEDERICO II. - COUNTRY: Italy"),
            _adjust_name(u'UNIVERSITA DEGLI STUDI DI NAPOLI FEDERICO II. - COUNTRY: ITALIA'),
        )
        self.assertEqual(
            _adjust_name(u"UNIVERSIDAD COMPLUTENSE DE MADRID - COUNTRY: ESPAÑA"),
            _adjust_name(u'UNIVERSIDAD COMPLUTENSE DE MADRID. - COUNTRY: ESPAÑA'),
        )


class TestUtilsGrouper(unittest.TestCase):
    pass


class TestUtilsWriter(unittest.TestCase):
    pass
