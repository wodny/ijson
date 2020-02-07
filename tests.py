# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import collections
import unittest
from decimal import Decimal
import threading
from importlib import import_module

from ijson import common
from ijson.compat import BytesIO, StringIO, b2s, IS_PY2, bytetype
from ijson.backends.python import basic_parse, Lexer
import warnings


JSON = b'''
{
  "docs": [
    {
      "null": null,
      "boolean": false,
      "true": true,
      "integer": 0,
      "double": 0.5,
      "exponent": 1.0e+2,
      "long": 10000000000,
      "string": "\\u0441\\u0442\\u0440\\u043e\\u043a\\u0430 - \xd1\x82\xd0\xb5\xd1\x81\xd1\x82",
      "\xc3\xb1and\xc3\xba": null
    },
    {
      "meta": [[1], {}]
    },
    {
      "meta": {"key": "value"}
    },
    {
      "meta": null
    }
  ]
}
'''
JSON_OBJECT = {
    "docs": [
        {
            "null": None,
            "boolean": False,
            "true": True,
            "integer": 0,
            "double": Decimal("0.5"),
            "exponent": 1e+2,
            "long": 10000000000,
            "string": "строка - тест",
            "ñandú": None
        },
        {
            "meta": [[1], {}]
        },
        {
            "meta": {
                "key": "value"
            }
        },
        {
            "meta": None
        }
    ]
}
JSON_PARSE_EVENTS = [
    ('', 'start_map', None),
    ('', 'map_key', 'docs'),
    ('docs', 'start_array', None),
    ('docs.item', 'start_map', None),
    ('docs.item', 'map_key', 'null'),
    ('docs.item.null', 'null', None),
    ('docs.item', 'map_key', 'boolean'),
    ('docs.item.boolean', 'boolean', False),
    ('docs.item', 'map_key', 'true'),
    ('docs.item.true', 'boolean', True),
    ('docs.item', 'map_key', 'integer'),
    ('docs.item.integer', 'number', 0),
    ('docs.item', 'map_key', 'double'),
    ('docs.item.double', 'number', Decimal('0.5')),
    ('docs.item', 'map_key', 'exponent'),
    ('docs.item.exponent', 'number', Decimal('1.0E+2')),
    ('docs.item', 'map_key', 'long'),
    ('docs.item.long', 'number', 10000000000),
    ('docs.item', 'map_key', 'string'),
    ('docs.item.string', 'string', 'строка - тест'),
    ('docs.item', 'map_key', 'ñandú'),
    ('docs.item.ñandú', 'null', None),
    ('docs.item', 'end_map', None),
    ('docs.item', 'start_map', None),
    ('docs.item', 'map_key', 'meta'),
    ('docs.item.meta', 'start_array', None),
    ('docs.item.meta.item', 'start_array', None),
    ('docs.item.meta.item.item', 'number', 1),
    ('docs.item.meta.item', 'end_array', None),
    ('docs.item.meta.item', 'start_map', None),
    ('docs.item.meta.item', 'end_map', None),
    ('docs.item.meta', 'end_array', None),
    ('docs.item', 'end_map', None),
    ('docs.item', 'start_map', None),
    ('docs.item', 'map_key', 'meta'),
    ('docs.item.meta', 'start_map', None),
    ('docs.item.meta', 'map_key', 'key'),
    ('docs.item.meta.key', 'string', 'value'),
    ('docs.item.meta', 'end_map', None),
    ('docs.item', 'end_map', None),
    ('docs.item', 'start_map', None),
    ('docs.item', 'map_key', 'meta'),
    ('docs.item.meta', 'null', None),
    ('docs.item', 'end_map', None),
    ('docs.item', 'start_map', None),
    ('docs', 'end_array', None),
    ('', 'end_map', None)
]
JSON_KVITEMS = [
    ("null", None),
    ("boolean", False),
    ("true", True),
    ("integer", 0),
    ("double", Decimal("0.5")),
    ("exponent", 1e+2),
    ("long", 10000000000),
    ("string", "строка - тест"),
    ("ñandú", None),
    ("meta", [[1], {}]),
    ("meta", {"key": "value"}),
    ("meta", None)
]
JSON_KVITEMS_META = [
    ('key', 'value')
]
JSON_EVENTS = [
    ('start_map', None),
        ('map_key', 'docs'),
        ('start_array', None),
            ('start_map', None),
                ('map_key', 'null'),
                ('null', None),
                ('map_key', 'boolean'),
                ('boolean', False),
                ('map_key', 'true'),
                ('boolean', True),
                ('map_key', 'integer'),
                ('number', 0),
                ('map_key', 'double'),
                ('number', Decimal('0.5')),
                ('map_key', 'exponent'),
                ('number', 100),
                ('map_key', 'long'),
                ('number', 10000000000),
                ('map_key', 'string'),
                ('string', 'строка - тест'),
                ('map_key', 'ñandú'),
                ('null', None),
            ('end_map', None),
            ('start_map', None),
                ('map_key', 'meta'),
                ('start_array', None),
                    ('start_array', None),
                        ('number', 1),
                    ('end_array', None),
                    ('start_map', None),
                    ('end_map', None),
                ('end_array', None),
            ('end_map', None),
            ('start_map', None),
                ('map_key', 'meta'),
                ('start_map', None),
                    ('map_key', 'key'),
                    ('string', 'value'),
                ('end_map', None),
            ('end_map', None),
            ('start_map', None),
                ('map_key', 'meta'),
                ('null', None),
            ('end_map', None),
        ('end_array', None),
    ('end_map', None),
]
SCALAR_JSON = b'0'
INVALID_JSONS = [
    b'["key", "value",]',      # trailing comma
    b'["key"  "value"]',       # no comma
    b'{"key": "value",}',      # trailing comma
    b'{"key": "value" "key"}', # no comma
    b'{"key"  "value"}',       # no colon
    b'invalid',                # unknown lexeme
    b'[1, 2] dangling junk'    # dangling junk
]
YAJL1_PASSING_INVALID = INVALID_JSONS[6]
INCOMPLETE_JSONS = [
    b'',
    b'"test',
    b'[',
    b'[1',
    b'[1,',
    b'{',
    b'{"key"',
    b'{"key":',
    b'{"key": "value"',
    b'{"key": "value",',
]
STRINGS_JSON = br'''
{
    "str1": "",
    "str2": "\"",
    "str3": "\\",
    "str4": "\\\\",
    "special\t": "\b\f\n\r\t"
}
'''
NUMBERS_JSON = b'[1, 1.0, 1E2]'
SURROGATE_PAIRS_JSON = br'"\uD83D\uDCA9"'
PARTIAL_ARRAY_JSONS = [
    (b'[1,', 1),
    (b'[1, 2 ', 1, 2),
    (b'[1, "abc"', 1, 'abc'),
    (b'[{"abc": [0, 1]}', {'abc': [0, 1]}),
    (b'[{"abc": [0, 1]},', {'abc': [0, 1]}),
]


class SingleReadFile(object):
    '''A bytes file that can be read only once'''

    str_type = bytetype

    def __init__(self, raw_value):
        self.raw_value = raw_value

    def read(self, size=-1):
        if size == 0:
            return self.str_type()
        val = self.raw_value
        if not val:
            raise AssertionError('read twice')
        self.raw_value = self.str_type()
        return val


class SingleReadFileStr(SingleReadFile):
    '''Like SingleReadFile, but reads strings'''

    str_type = str

    def __init__(self, raw_value):
        super(SingleReadFileStr, self).__init__(b2s(raw_value))

class Parse(object):
    '''
    Base class for parsing tests that is used to create test cases for each
    available backends.
    '''
    def test_basic_parse(self):
        events = list(self.backend.basic_parse(BytesIO(JSON)))
        self.assertEqual(events, JSON_EVENTS)

    def test_parse(self):
        events = list(self.backend.parse(BytesIO(JSON)))
        self.assertEqual(events, JSON_PARSE_EVENTS)

    def test_basic_parse_threaded(self):
        thread = threading.Thread(target=self.test_basic_parse)
        thread.start()
        thread.join()

    def test_scalar(self):
        events = list(self.backend.basic_parse(BytesIO(SCALAR_JSON)))
        self.assertEqual(events, [('number', 0)])

    def test_strings(self):
        events = list(self.backend.basic_parse(BytesIO(STRINGS_JSON)))
        strings = [value for event, value in events if event == 'string']
        self.assertEqual(strings, ['', '"', '\\', '\\\\', '\b\f\n\r\t'])
        self.assertTrue(('map_key', 'special\t') in events)

    def test_surrogate_pairs(self):
        event = next(self.backend.basic_parse(BytesIO(SURROGATE_PAIRS_JSON)))
        parsed_string = event[1]
        self.assertEqual(parsed_string, '💩')

    def test_numbers(self):
        events = list(self.backend.basic_parse(BytesIO(NUMBERS_JSON)))
        types = [type(value) for event, value in events if event == 'number']
        self.assertEqual(types, [int, Decimal, Decimal])

    def test_invalid(self):
        for json in INVALID_JSONS:
            # Yajl1 doesn't complain about additional data after the end
            # of a parsed object. Skipping this test.
            if self.__class__.__name__ == 'YajlParse' and json == YAJL1_PASSING_INVALID:
                continue
            with self.assertRaises(common.JSONError) as cm:
                list(self.backend.basic_parse(BytesIO(json)))

    def test_incomplete(self):
        for json in INCOMPLETE_JSONS:
            with self.assertRaises(common.IncompleteJSONError):
                list(self.backend.basic_parse(BytesIO(json)))

    def test_utf8_split(self):
        buf_size = JSON.index(b'\xd1') + 1
        try:
            events = list(self.backend.basic_parse(BytesIO(JSON), buf_size=buf_size))
        except UnicodeDecodeError:
            self.fail('UnicodeDecodeError raised')

    def test_lazy(self):
        # shouldn't fail since iterator is not exhausted
        self.backend.basic_parse(BytesIO(INVALID_JSONS[0]))
        self.assertTrue(True)

    def test_boundary_lexeme(self):
        buf_size = JSON.index(b'false') + 1
        events = list(self.backend.basic_parse(BytesIO(JSON), buf_size=buf_size))
        self.assertEqual(events, JSON_EVENTS)

    def test_boundary_whitespace(self):
        buf_size = JSON.index(b'   ') + 1
        events = list(self.backend.basic_parse(BytesIO(JSON), buf_size=buf_size))
        self.assertEqual(events, JSON_EVENTS)

    def test_api(self):
        self.assertTrue(list(self.backend.items(BytesIO(JSON), '')))
        self.assertTrue(list(self.backend.parse(BytesIO(JSON))))

    def test_items_twodictlevels(self):
        f = BytesIO(b'{"meta":{"view":{"columns":[{"id": -1}, {"id": -2}]}}}')
        ids = list(self.backend.items(f, 'meta.view.columns.item.id'))
        self.assertEqual(2, len(ids))
        self.assertListEqual([-2,-1], sorted(ids))

    def test_kvitems(self):
        kvitems = list(self.backend.kvitems(BytesIO(JSON), 'docs.item'))
        self.assertEqual(JSON_KVITEMS, kvitems)

    def test_kvitems_toplevel(self):
        kvitems = list(self.backend.kvitems(BytesIO(JSON), ''))
        self.assertEqual(1, len(kvitems))
        key, value = kvitems[0]
        self.assertEqual('docs', key)
        self.assertEqual(JSON_OBJECT['docs'], value)

    def test_kvitems_empty(self):
        kvitems = list(self.backend.kvitems(BytesIO(JSON), 'docs'))
        self.assertEqual([], kvitems)

    def test_kvitems_twodictlevels(self):
        f = BytesIO(b'{"meta":{"view":{"columns":[{"id": -1}, {"id": -2}]}}}')
        view = list(self.backend.kvitems(f, 'meta.view'))
        self.assertEqual(1, len(view))
        key, value = view[0]
        self.assertEqual('columns', key)
        self.assertEqual([{'id': -1}, {'id': -2}], value)

    def test_kvitems_different_underlying_types(self):
        kvitems = list(self.backend.kvitems(BytesIO(JSON), 'docs.item.meta'))
        self.assertEqual(JSON_KVITEMS_META, kvitems)

    def test_multiple_values(self):
        if not self.supports_multiple_values:
            return
        basic_parse = self.backend.basic_parse
        items = lambda x, **kwargs: self.backend.items(x, '', **kwargs)
        multiple_values = JSON + JSON + JSON
        for func in (basic_parse, items):
            generator = func(BytesIO(multiple_values))
            self.assertRaises(common.JSONError, list, generator)
            generator = func(BytesIO(multiple_values), multiple_values=False)
            self.assertRaises(common.JSONError, list, generator)
            generator = func(BytesIO(multiple_values), multiple_values=True)
            result = list(generator)
            if func == basic_parse:
                self.assertEqual(result, JSON_EVENTS + JSON_EVENTS + JSON_EVENTS)
            else:
                self.assertEqual(result, [JSON_OBJECT, JSON_OBJECT, JSON_OBJECT])

    def test_map_type(self):
        obj = next(self.backend.items(BytesIO(JSON), ''))
        self.assertTrue(isinstance(obj, dict))
        obj = next(self.backend.items(BytesIO(JSON), '', map_type=collections.OrderedDict))
        self.assertTrue(isinstance(obj, collections.OrderedDict))

    def test_string_stream(self):
        with warnings.catch_warnings(record=True) as warns:
            events = list(self.backend.basic_parse(StringIO(b2s(JSON))))
            self.assertEqual(events, JSON_EVENTS)
        if self.warn_on_string_stream:
            self.assertEqual(len(warns), 1)
            self.assertEqual(DeprecationWarning, warns[0].category)

    def test_item_building_greediness(self):
        self._test_item_iteration_validity(BytesIO)

    def test_lazy_file_reading(self):
        file_type = SingleReadFile
        if self.backend.__name__.endswith('.python'):
            if IS_PY2:
                # We know it doesn't work because because the decoder itself
                # is quite eager on its reading
                return
            file_type = SingleReadFileStr
        self._test_item_iteration_validity(file_type)

    def _test_item_iteration_validity(self, file_type):
        for json in PARTIAL_ARRAY_JSONS:
            json, expected_items = json[0], json[1:]
            iterable = self.backend.items(file_type(json), 'item')
            for expected_item in expected_items:
                self.assertEqual(expected_item, next(iterable))

# Generating real TestCase classes for each importable backend
for name in ['python', 'yajl', 'yajl2', 'yajl2_cffi', 'yajl2_c']:
    try:
        classname = '%sParse' % ''.join(p.capitalize() for p in name.split('_'))
        if IS_PY2:
            classname = classname.encode('ascii')

        locals()[classname] = type(
            classname,
            (unittest.TestCase, Parse),
            {
                'backend': import_module('ijson.backends.%s' % name),
                'supports_multiple_values': name != 'yajl',
                'warn_on_string_stream': name != 'python' and not IS_PY2
            },
        )
    except ImportError:
        pass


class Common(unittest.TestCase):
    '''
    Backend independent tests. They all use basic_parse imported explicitly from
    the python backend to generate parsing events.
    '''
    def test_object_builder(self):
        builder = common.ObjectBuilder()
        for event, value in basic_parse(BytesIO(JSON)):
            builder.event(event, value)
        self.assertEqual(builder.value, JSON_OBJECT)

    def test_scalar_builder(self):
        builder = common.ObjectBuilder()
        for event, value in basic_parse(BytesIO(SCALAR_JSON)):
            builder.event(event, value)
        self.assertEqual(builder.value, 0)

    def test_parse(self):
        events = common.parse(basic_parse(BytesIO(JSON)))
        events = [value
            for prefix, event, value in events
            if prefix == 'docs.item.meta.item.item'
        ]
        self.assertEqual(events, [1])

    def test_items(self):
        events = basic_parse(BytesIO(JSON))
        meta = list(common.items(common.parse(events), 'docs.item.meta'))
        self.assertEqual(meta, [
            [[1], {}],
            {'key': 'value'},
            None,
        ])

class Stream(unittest.TestCase):
    def test_bytes(self):
        l = Lexer(BytesIO(JSON))
        self.assertEqual(next(l)[1], '{')

    def test_string(self):
        l = Lexer(StringIO(JSON.decode('utf-8')))
        self.assertEqual(next(l)[1], '{')


if __name__ == '__main__':
    unittest.main()
