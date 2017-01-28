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

mytables = wsl.parse_db(schemastr=myschema.spec, dbstr="""
parent foo
parent bar
child foo 0 one
child foo 1 two
child bar 5 quux
child bar 4 baz
""")

wsl.check_database_integrity(myschema, mytables)


def lookup_primformatter(primtype):
    # inconsistent naming... :(
    domain = myschema.domains.get(primtype)
    if domain is None:
        assert False
    return domain.funcs.encode


def lookup_primparser(primtype):
    # inconsistent naming... :(
    domain = myschema.domains.get(primtype)
    if domain is None:
        assert False
    return lambda x,i: domain.funcs.decode(domain.funcs.wsllex(x, i))


def json_repr(x):
    return json.dumps(x, sort_keys=True, indent=2, ensure_ascii=False)


def testit():
    objs = wslh.rows2objects(myspec, mytables)
    print(objs)

    newtables = wslh.objects2rows(myspec, objs)

    print('NEWTABLES')
    print(wsl.format_db(myschema, newtables, True))

    x = wslh.objects2text(lookup_primformatter, myspec, objs)
    print(x)

    y = wslh.text2objects(lookup_primparser, myspec, x)

testit()
