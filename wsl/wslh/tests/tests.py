import json

import wsl
import wsl.wslh as wslh


def canonical_json(objs):
    return json.dumps(objs, ensure_ascii=True, sort_keys=True)


schemastr = """
DOMAIN Int Int
TABLE foo Int Int Int
TABLE bar Int Int
REFERENCE foobar foo * * c => bar c *
"""


dbstr = """
foo 1 2 3
foo 4 5 6
bar 3 666
bar 6 1024
bar 42 0
"""


myschema = wsl.parse_schema(schemastr)


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


mytables = wsl.parse_db(schemastr=schemastr, dbstr=dbstr)


myobject = {
    'bars': {
        3: { 'c': 3, 'd': 666, 's': { 'a': 1, 'b': 2 } },
        6: { 'c': 6, 'd': 1024, 's': { 'a': 4, 'b': 5 } },
        42: { 'c': 42, 'd': 0, 's': None }
    }
}


myjsonobject = {
    'bars': {
        '3': { 'c': 3, 'd': 666, 's': { 'a': 1, 'b': 2 } },
        '6': { 'c': 6, 'd': 1024, 's': { 'a': 4, 'b': 5 } },
        '42': { 'c': 42, 'd': 0, 's': None }
    }
}


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


def lookup_primlexer(primtype):
    # inconsistent naming... :(
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    return domain.funcs.wsllex


def lookup_primunlexer(primtype):
    # inconsistent naming... :(
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    return domain.funcs.wslunlex


def lookup_primdecoder(primtype):
    # inconsistent naming... :(
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    return domain.funcs.decode


def lookup_primencoder(primtype):
    # inconsistent naming... :(
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    return domain.funcs.format


def lookup_primwriter(primtype):
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    encoder = domain.funcs.encode
    unlexer = domain.funcs.wslunlex
    def primwriter(value):
        return unlexer(encoder(value))
    return primwriter


def lookup_jsontype(primtype):
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    return domain.funcs.jsontype


def lookup_jsonformatter(primtype, is_dict_key):
    domain = myschema.domains.get(primtype)
    if domain is None:
        return None
    encode = domain.funcs.encode
    jsonunlex = wsl.make_jsonunlex(domain.funcs.jsontype, is_dict_key)
    def jsonformatter(obj):
        return jsonunlex(encode(obj))
    return jsonformatter


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

    objects = wslh.rows2objects(myspec, mytables)

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

    tables = wslh.objects2rows(myspec, myobject)

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

    objects = wslh.text2objects(wsl.make_make_wslreader(myschema), myspec, mytext)

    print(objects)

    return objects


def test_objects2text():
    print()
    print('TESTING objects2text()...')
    print('=========================')
    print()

    text = wslh.objects2text(wsl.make_make_wslwriter(myschema), myspec, myobject)

    print(text)

    return text


def test_json2objects():
    print()
    print('TESTING json2objects()...')
    print('=========================')
    print()

    objects = wslh.json2objects(wsl.make_make_jsonreader(myschema), myspec, myjsonobject)

    print(objects)

    return objects


def test_objects2json():
    print()
    print('TESTING objects2json()...')
    print('=========================')
    print()

    jsonobject = wslh.objects2json(wsl.make_make_jsonwriter(myschema), myspec, myobject)

    print(jsonobject)

    return jsonobject


if __name__ == '__main__':
    objects = test_rows2objects()
    tables = test_objects2rows()
    objects2 = test_text2objects()
    text = test_objects2text()
    objects2 = test_json2objects()
    jsonobject = test_objects2json()

    assert canonical_json(objects) == canonical_json(myobject)
    assert canonical_json(tables) == canonical_json(mytables)
    assert objects == objects2
    assert text == mytext
    assert jsonobject == myjsonobject
