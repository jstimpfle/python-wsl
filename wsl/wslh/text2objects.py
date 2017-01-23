import re

from .datatypes import Value, Struct, Option, Set, List, Dict


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
        lexer = dct.get(kw)
        if lexer is None:
            raise make_parse_exc('Found unexpected field "%s"' %(kw,), text, i)
        i, val = lexer(text, i)
        out.append((kw, val))
    return i, out


def space_and_then(valuelexer):
    def space_and_then_lexer(text, i):
        i = parse_space(text, i)
        i, v = valuelexer(text, i)
        return i, v
    return space_and_then_lexer


def newline_and_then(valuelexer):
    def newline_and_then_lexer(text, i):
        i = parse_newline(text, i)
        i, v = valuelexer(text, i)
        return i, v
    return newline_and_then_lexer


def make_keyvalue_lexer(keylexer, valuelexer):
    def keyvalue_lexer(text, i):
        i = parse_space(text, i)
        i, k = keylexer(text, i)
        i = parse_newline(text, i)
        i, v = valuelexer(text, i)
        return i, (k, v)
    return keyvalue_lexer


def make_struct_lexer(dct, indent):
    def struct_lexer(text, i):
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
    return struct_lexer


def make_option_lexer(lexer):
    def option_lexer(text, i):
        end = len(text)
        if i < end and text[i] == '!':
            i, val = lexer(text, i+1)
        elif i < end and text[i] == '?':
            i, val = i+1, None
        else:
            raise make_parse_exc('Expected option ("?", or "!" followed by value)', text, i)
        return i, val
    return option_lexer


def make_dict_lexer(key_lexer, val_lexer, indent):
    item_lexer = make_keyvalue_lexer(key_lexer, val_lexer)
    def dict_lexer(text, i):
        i, items = parse_block({ 'value': item_lexer }, indent, text, i)
        out = {}
        for _, (k, v) in items:
            if k in out:
                raise make_parse_exc('Key "%s" used multiple times in this block' %(k,), text, i)
            out[k] = v
        return i, out
    return dict_lexer


def make_list_lexer(lexer, indent):
    def list_lexer(text, i):
        dct = { 'value': lexer }
        i, items = parse_block(dct, indent, text, i)
        out = []
        for _, v in items:
            out.append(v)
        return i, out
    return list_lexer


def run_lexer(lexer, text):
    i, r = lexer(text, 0)
    if i != len(text):
        raise make_parse_exc('Unconsumed text', text, i)
    return r


def make_lexer_from_spec(lookup_primlexer, spec, indent):
    nextindent = indent + INDENTSPACES
    typ = type(spec)

    if typ == Value:
        lexer = lookup_primlexer(spec.primtype)
        if lexer is None:
            raise ValueError('There is no lexer for datatype "%s"' %(spec.primtype,))
        return lexer

    elif typ == Struct:
        dct = {}
        for k, v in spec.childs.items():
            sublexer = make_lexer_from_spec(lookup_primlexer, v, nextindent)
            if type(v) in [Value, Option]:
                dct[k] = space_and_then(sublexer)
            else:
                dct[k] = newline_and_then(sublexer)
        return make_struct_lexer(dct, indent)

    elif typ == Option:
        sublexer = make_lexer_from_spec(lookup_primlexer, spec.childs['_val_'], indent)
        return make_option_lexer(sublexer)

    elif typ == List:
        val_lexer = make_lexer_from_spec(lookup_primlexer, spec.childs['_val_'], nextindent)
        if type(spec.childs['_val_']) == Value:
            p = space_and_then(val_lexer)
        else:
            p = newline_and_then(val_lexer)
        return make_list_lexer(p, indent)

    elif typ == Dict:
        key_lexer = make_lexer_from_spec(lookup_primlexer, spec.childs['_key_'], nextindent)
        val_lexer = make_lexer_from_spec(lookup_primlexer, spec.childs['_val_'], nextindent)
        return make_dict_lexer(key_lexer, val_lexer, indent)

    assert False  # missing case


def text2objects(lookup_primlexer, spec, text):
    assert isinstance(text, str)
    lexer = make_lexer_from_spec(lookup_primlexer, spec, 0)
    return run_lexer(lexer, text)
