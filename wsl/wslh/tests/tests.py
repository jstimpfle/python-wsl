import json

import wsl
import wslh


myschema = wsl.parse_schema("""
DOMAIN Int Int
TABLE foo Int Int Int
TABLE bar Int Int
REFERENCE foobar foo * * c => bar c *
""")


myspec = wslh.parse_spec(myschema, """\
bars: dict for (c d) (bar c d)
    _key_: value c
    _val_: struct
        c: value c
        d: value d
        s: struct for (a b) (foo a b c)
            a: value a
            b: value b
""")


mydatabase = {
    'foo': [(1, 2, 3), (4, 5, 6)],
    'bar': [(3, 666), (6, 1024), (42, 0)]
}


myobject = {
    'bars': {
        3: { 'c': 3, 'd': 666, 's': { 'a': 1, 'b': 2 } },
        6: { 'c': 6, 'd': 1024, 's': { 'a': 4, 'b': 5 } },
        42: { 'c': 42, 'd': 0, 's': None }
    }
}


mytext = """\
bars
    value 3
        c 3
        d 666
        s
            a 1
            b 2
    value 6
        c 6
        d 1024
        s
            a 4
            b 5
    value 42
        c 42
        d 0
"""


def json_repr(x):
    return json.dumps(x, sort_keys=True, indent=2, ensure_ascii=False)


def test_rows2objects():
    print()
    print('TESTING rows2objects()...')
    print('=========================')
    print()

    print('Database:')
    print('=========')
    for key, rows in sorted(mydatabase.items()):
        print(key)
        print('-' * len(key))
        for row in sorted(rows):
            print(row)
        print()

    objects = wslh.rows2objects(myspec, mydatabase)

    assert isinstance(objects, dict)

    print('RESULT')
    print('======')
    print(json_repr(objects))

    return objects


def test_objects2rows():
    print()
    print('TESTING objects2rows()...')
    print('=========================')
    print()

    print('Objects:')
    print('========')
    print(json_repr(myobject))

    database = wslh.objects2rows(myobject, myspec)

    print()
    print('RESULTS')
    print('=======')
    print()
    for table in ['bar', 'foo']:
        print(table)
        print('=' * len(table))
        for row in database[table]:
            print(row)
        print()

    return database


def test_text2objects():
    print()
    print('TESTING text2objects()...')
    print('=========================')
    print()

    def lookup_primparser(primtype):
        if primtype == 'Int':
            return wslh.parse_int
        elif primtype == 'String':
            return wslh.parse_string
        elif primtype.endswith('ID'):
            return wslh.parse_identifier
        else:
            assert False

    objects = wslh.text2objects(lookup_primparser, myspec, mytext)

    print(objects)

    return objects


if __name__ == '__main__':
    objects = test_rows2objects()
    database = test_objects2rows()
    objects2 = test_text2objects()

    assert json_repr(objects) == json_repr(myobject)
    assert json_repr(database) == json_repr(mydatabase)
    assert objects == objects2
