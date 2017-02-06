import re

from ..exceptions import ParseError
from ..schema import Schema
from ..lexwsl import make_make_wslreader
from .datatypes import Value, Struct, Option, Set, List, Dict


INDENTSPACES = 4


def _chardesc(text, i):
    if i >= len(text):
        return '(EOL)'

    return '"' + text[i] + '"'


def parse_space(text, i):
    start = i
    end = len(text)
    if i >= end or text[i] != ' ':
        raise LexError('Space character', text, i, i, 'Expected space character (0x20) but found 0x%.2x' %(ord(text[i]),))
    return i + 1


def parse_newline(text, i):
    start = i
    end = len(text)
    if i >= end or text[i] != '\n':
        raise LexError('Newline character', text, i, i, 'Expected newline character (0x0a) but found 0x%.2x' %(ord(text[i]),))
    return i + 1


def parse_keyword(text, i):
    start = i
    end = len(text)
    while i < end and text[i].isalpha():
        i += 1
    if i == start:
        raise LexError('Keyword', text, i, i, 'Found invalid character "%s with no valid consumed characters' %(_chardesc(text, i),))
    return i, text[start:i]


def parse_block(dct, indent, text, i):
    start = i
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
        reader = dct.get(kw)
        if reader is None:
            raise ParseError('Found unexpected field "%s"' %(kw,), text, i)
        i, val = reader(text, i)
        out.append((kw, val))
    return i, out


def space_and_then(valuereader):
    def space_and_then_reader(text, i):
        i = parse_space(text, i)
        i, v = valuereader(text, i)
        return i, v
    return space_and_then_reader


def newline_and_then(valuereader):
    def newline_and_then_reader(text, i):
        i = parse_newline(text, i)
        i, v = valuereader(text, i)
        return i, v
    return newline_and_then_reader


def make_keyvalue_reader(keyreader, valuereader):
    def keyvalue_reader(text, i):
        i = parse_space(text, i)
        i, k = keyreader(text, i)
        i = parse_newline(text, i)
        i, v = valuereader(text, i)
        return i, (k, v)
    return keyvalue_reader


def make_struct_reader(dct, indent):
    def struct_reader(text, i):
        i, items = parse_block(dct, indent, text, i)
        struct = {}
        for k, v in items:
            if k not in dct.keys():
                raise ParseError('Invalid key: %s' %(k,), text, i)
            if k in items:
                raise ParseError('Duplicate key: %s' %(k,), text, i)
            struct[k] = v
        for k in dct.keys():
            struct.setdefault(k, None)
        return i, struct
    return struct_reader


def make_option_reader(reader, indent):
    def option_reader(text, i):
        end = len(text)
        if i < end and text[i] == '!':
            i += 1
            i, val = reader(text, i)
        elif i < end and text[i] == '?':
            i, val = i+1, None
        else:
            raise ParseError('Expected option ("?", or "!" followed by value)', text, i)
        return i, val
    return option_reader


def make_set_reader(reader, indent):
    def set_reader(text, i):
        dct = { 'val': reader }
        i, items = parse_block(dct, indent, text, i)
        out = set()
        for _, v in items:
            out.add(v)
        return i, out
    return set_reader


def make_list_reader(reader, indent):
    def list_reader(text, i):
        dct = { 'val': reader }
        i, items = parse_block(dct, indent, text, i)
        out = []
        for _, v in items:
            out.append(v)
        return i, out
    return list_reader


def make_dict_reader(key_reader, val_reader, indent):
    item_reader = make_keyvalue_reader(key_reader, val_reader)
    def dict_reader(text, i):
        start = i
        i, items = parse_block({ 'val': item_reader }, indent, text, i)
        out = {}
        for _, (k, v) in items:
            if k in out:
                raise ParseError('Parse WSLH dict', text, start, i, 'Key "%s" used multiple times in this block' %(k,))
            out[k] = v
        return i, out
    return dict_reader


def run_reader(reader, text):
    i, r = reader(text, 0)
    if i != len(text):
        raise ParseError('Unconsumed text', text, i)
    return r


def make_lexer_from_spec(make_reader, spec, indent):
    nextindent = indent + INDENTSPACES
    typ = type(spec)

    if typ == Value:
        reader = make_reader(spec.primtype)
        if reader is None:
            raise ValueError('There is no reader for datatype "%s"' %(spec.primtype,))
        return reader

    elif typ == Struct:
        dct = {}
        for k, v in spec.childs.items():
            subreader = make_lexer_from_spec(make_reader, v, nextindent)
            if type(v) in [Value, Option]:
                dct[k] = space_and_then(subreader)
            else:
                dct[k] = newline_and_then(subreader)
        return make_struct_reader(dct, indent)

    elif typ == Option:
        subreader = make_lexer_from_spec(make_reader, spec.childs['_val_'], indent)
        if type(spec.childs['_val_']) == Value:
            p = space_and_then(subreader)
        else:
            p = newline_and_then(subreader)
        return make_option_reader(subreader, indent)

    elif typ == Set:
        val_reader = make_lexer_from_spec(make_reader, spec.childs['_val_'], indent)
        if type(spec.childs['_val_']) == Value:
            p = space_and_then(val_reader)
        else:
            p = newline_and_then(val_reader)
        return make_set_reader(p, indent)

    elif typ == List:
        val_reader = make_lexer_from_spec(make_reader, spec.childs['_val_'], nextindent)
        if type(spec.childs['_val_']) == Value:
            p = space_and_then(val_reader)
        else:
            p = newline_and_then(val_reader)
        return make_list_reader(p, indent)

    elif typ == Dict:
        key_reader = make_lexer_from_spec(make_reader, spec.childs['_key_'], nextindent)
        val_reader = make_lexer_from_spec(make_reader, spec.childs['_val_'], nextindent)
        return make_dict_reader(key_reader, val_reader, indent)

    assert False  # missing case


def text2objects(schema, spec, text):
    if not isinstance(schema, Schema):
        raise TypeError()
    if not isinstance(text, str):
        raise TypeError()
    reader = make_lexer_from_spec(make_make_wslreader(schema), spec, 0)
    return run_reader(reader, text)
