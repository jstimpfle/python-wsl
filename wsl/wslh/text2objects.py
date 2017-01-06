import re

from .datatypes import Value, Struct, List, Dict


INDENTSPACES = 4


class ParseException(Exception):
    def __init__(self, msg, lineno, charno):
        self.msg = msg
        self.lineno = lineno
        self.charno = charno

    def __str__(self):
        return 'At %d:%d: %s' %(self.lineno, self.charno, self.msg)


def make_parse_exc(msg, text, i):
    lines = text[:i].split('\n')
    lineno = len(lines)
    charno = i + 1 - sum(len(l) + 1 for l in lines[:-1])
    return ParseException(msg, lineno, charno)


def parse_space(text, i):
    end = len(text)
    start = i
    if i >= end or text[i] != ' ':
        raise make_parse_exc('Space character expected', text, i)
    return i + 1


def parse_newline(text, i):
    end = len(text)
    start = i
    if i >= end or text[i] != '\n':
        raise make_parse_exc('End of line (\\n) expected', text, i)
    return i + 1


def parse_keyword(text, i):
    end = len(text)
    start = i
    while i < end and text[i].isalpha():
        i += 1
    if i == start:
        raise make_parse_exc('Keyword expected', text, i)
    return i, text[start:i]


def parse_identifier(text, i):
    end = len(text)
    start = i
    m = re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*', text[i:])
    if m is None:
        raise make_parse_exc('Identifier expected', text, i)
    i += m.end(0)
    return i, text[start:i]


def parse_string(text, i):
    end = len(text)
    start = i
    m = re.match(r'^\[[^]\n]*\]', text[i:])
    if m is None:
        raise make_parse_exc('String [in square bracket style] expected but found %s' %(text[i:],), text, i)
    i += m.end(0)
    return i, text[start+1:i-1]


def parse_int(text, i):
    end = len(text)
    start = i
    m = re.match(r'^(0|-?[1-9][0-9]*)', text[i:])
    if m is None:
        raise make_parse_exc('Integer expected', text, i)
    i += m.end(0)
    return i, int(text[start:i])


def parse_block(dct, indent, text, i):
    end = len(text)
    out = []
    while True:
        while i < end and text[i] == '\n':
            i += 1
        if i == end:
            break
        if not text[i:].startswith(' ' * indent):
            break
        i += indent
        i, kw = parse_keyword(text, i)
        parser = dct.get(kw)
        if parser is None:
            raise make_parse_exc('Found unexpected field "%s"' %(kw,), text, i)
        i, val = parser(text, i)
        out.append((kw, val))
    return i, out


def space_and_then(valueparser):
    def space_and_then_parser(text, i):
        i = parse_space(text, i)
        i, v = valueparser(text, i)
        return i, v
    return space_and_then_parser


def newline_and_then(valueparser):
    def newline_and_then_parser(text, i):
        i = parse_newline(text, i)
        i, v = valueparser(text, i)
        return i, v
    return newline_and_then_parser


def make_keyvalue_parser(keyparser, valueparser):
    def keyvalue_parser(text, i):
        i = parse_space(text, i)
        i, k = keyparser(text, i)
        i = parse_newline(text, i)
        i, v = valueparser(text, i)
        return i, (k, v)
    return keyvalue_parser


def make_struct_parser(dct, indent):
    def struct_parser(text, i):
        i, items = parse_block(dct, indent, text, i)
        struct = {}
        for k, v in items:
            if k not in dct.keys():
                raise make_parse_exc('Invalid key: %s' %(k,), text, i)
            if k in items:
                raise make_parse_exc('Duplicate key: %s' %(k,), text, i)
            struct[k] = v
        for k in dct.keys():
            struct.setdefault(k, None)
        return i, struct
    return struct_parser


def make_dict_parser(key_parser, val_parser, indent):
    item_parser = make_keyvalue_parser(key_parser, val_parser)
    def dict_parser(text, i):
        i, items = parse_block({ 'value': item_parser }, indent, text, i)
        out = {}
        for _, (k, v) in items:
            if k in out:
                raise make_parse_exc('Key "%s" used multiple times in this block' %(k,), text, i)
            out[k] = v
        return i, out
    return dict_parser


def make_list_parser(parser, indent):
    def list_parser(text, i):
        dct = { 'value': parser }
        i, items = parse_block(dct, indent, text, i)
        out = []
        for _, v in items:
            out.append(v)
        return i, out
    return list_parser


def doparse(parser, text):
    i, r = parser(text, 0)
    if i != len(text):
        raise make_parse_exc('Unconsumed text', text, i)
    return r


def make_parser_from_spec(lookup_primparser, spec, indent):
    nextindent = indent + INDENTSPACES
    typ = type(spec)

    if typ == Value:
        parser = lookup_primparser(spec.primtype)
        if parser is None:
            raise ValueError('There is no parser for datatype "%s"' %(spec.primtype,))
        return parser

    elif typ == Struct:
        dct = {}
        for k, v in spec.childs.items():
            subparser = make_parser_from_spec(lookup_primparser, v, nextindent)
            if type(v) == Value:
                dct[k] = space_and_then(subparser)
            else:
                dct[k] = newline_and_then(subparser)
        return make_struct_parser(dct, indent)

    elif typ == List:
        val_parser = make_parser_from_spec(lookup_primparser, spec.childs['_val_'], nextindent)
        if type(spec.childs['_val_']) == Value:
            p = space_and_then(val_parser)
        else:
            p = newline_and_then(val_parser)
        return make_list_parser(p, indent)

    elif typ == Dict:
        key_parser = make_parser_from_spec(lookup_primparser, spec.childs['_key_'], nextindent)
        val_parser = make_parser_from_spec(lookup_primparser, spec.childs['_val_'], nextindent)
        return make_dict_parser(key_parser, val_parser, indent)

    assert False  # missing case


def text2objects(lookup_primparser, spec, text):
    assert isinstance(text, str)
    parser = make_parser_from_spec(lookup_primparser, spec, 0)
    return doparse(parser, text)
