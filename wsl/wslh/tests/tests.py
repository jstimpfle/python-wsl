import json

import wsl
import wsl.wslh as wslh


def canonical_json(objs):
    return json.dumps(objs, ensure_ascii=True, sort_keys=True)


myschema = wsl.parse_schema("""
DOMAIN Int Int
TABLE foo Int Int Int
TABLE bar Int Int
REFERENCE foobar foo * * c => bar c *
""")

_, mytables = wsl.parse_db(schema=myschema, dbstr="""
foo 1 2 3
foo 4 5 6
bar 3 666
bar 6 1024
bar 42 0
""")

myspec = wslh.parse_spec(myschema, """\
bars: dict for (c d) (bar c d)
    _key_: value c
    _val_: struct
        c: value c
        d: value d
        s: option for (a b) (foo a b c)
            _val_: struct
                a: value a
                b: value b
""")

myobject = {
    'bars': {
        3: { 'c': 3, 'd': 666, 's': { 'a': 1, 'b': 2 } },
        6: { 'c': 6, 'd': 1024, 's': { 'a': 4, 'b': 5 } },
        42: { 'c': 42, 'd': 0, 's': None }
    }
}

myjson = """
{
    "bars": {
        "3": { "c": 3, "d": 666, "s": { "a": 1, "b": 2 } },
        "6": { "c": 6, "d": 1024, "s": { "a": 4, "b": 5 } },
        "42": { "c": 42, "d": 0, "s": null }
    }
}
"""

mytext = """\
bars
    val 3
        c 3
        d 666
        s !
            a 1
            b 2
    val 6
        c 6
        d 1024
        s !
            a 4
            b 5
    val 42
        c 42
        d 0
        s ?
"""


def test_rows2objects():
    print()
    print('TESTING rows2objects()...')
    print('=========================')
    print()

    print('Database:')
    print('=========')
    for key, rows in sorted(mytables.items()):
        print(key)
        print('-' * len(key))
        for row in sorted(rows):
            print(row)
        print()

    objects = wslh.rows2objects(myschema, myspec, mytables)

    assert isinstance(objects, dict)

    print('RESULT')
    print('======')
    print(canonical_json(objects))

    return objects


def test_objects2rows():
    print()
    print('TESTING objects2rows()...')
    print('=========================')
    print()

    print('Objects:')
    print('========')
    print(canonical_json(myobject))

    tables = wslh.objects2rows(myschema, myspec, myobject)

    print()
    print('RESULTS')
    print('=======')
    print()
    for table in ['bar', 'foo']:
        print(table)
        print('=' * len(table))
        for row in tables[table]:
            print(row)
        print()

    return tables


def test_text2objects():
    print()
    print('TESTING text2objects()...')
    print('=========================')
    print()

    objects = wslh.text2objects(myschema, myspec, mytext)

    print(objects)

    return objects


def test_objects2text():
    print()
    print('TESTING objects2text()...')
    print('=========================')
    print()

    text = wslh.objects2text(myschema, myspec, myobject)

    print(text)

    return text


def test_json2objects():
    print()
    print('TESTING json2objects()...')
    print('=========================')
    print()

    objects = wslh.json2objects(myschema, myspec, myjson)

    print(objects)

    return objects


def test_objects2json():
    print()
    print('TESTING objects2json()...')
    print('=========================')
    print()

    thejson = wslh.objects2json(myschema, myspec, myobject)

    print(thejson)

    return thejson


if __name__ == '__main__':
    objects = test_rows2objects()
    tables = test_objects2rows()
    objects2 = test_text2objects()
    text = test_objects2text()
    objects2 = test_json2objects()
    thejson = test_objects2json()

    assert canonical_json(objects) == canonical_json(myobject)
    assert canonical_json(tables) == canonical_json(mytables)
    assert objects == objects2
    assert text == mytext
    # TODO: objects2json.py assert thejson == myjson
