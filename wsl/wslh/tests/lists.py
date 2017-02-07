import json

import wsl
import wsl.wslh as wslh


myschema = wsl.parse_schema("""\
DOMAIN Int Int
DOMAIN ID ID
TABLE parent ID
TABLE child ID Int ID
KEY parent parent P
REFERENCE child child P * * => parent P
""")


myspec = wslh.parse_spec(myschema, """\
Test: dict for (p) (parent p)
    _key_: value p
    _val_: list for (i v) (child p i v)
        _idx_: value i
        _val_: value v
""")

_, mytables = wsl.parse_db(schema=myschema, dbstr="""
parent foo
parent bar
child foo 0 one
child foo 1 two
child bar 5 quux
child bar 4 baz
""")

wsl.check_database_integrity(myschema, mytables)


def json_repr(x):
    return json.dumps(x, sort_keys=True, indent=2, ensure_ascii=False)


def testit():
    objs = wslh.rows2objects(myschema, myspec, mytables)
    print(objs)

    newtables = wslh.objects2rows(myschema, myspec, objs)

    print('NEWTABLES')
    print(wsl.format_db(myschema, newtables, True))

    x = wslh.objects2text(myschema, myspec, objs)
    print(x)

    y = wslh.text2objects(myschema, myspec, x)

testit()
