import json

from ..exceptions import ParseError, LexError
from .datatypes import Value, Struct, Option, Set, List, Dict
from ..schema import Schema
from ..lexjson import lex_json_string
from ..lexjson import lex_json_null
from ..lexjson import lex_json_whitespace
from ..lexjson import lex_json_openbrace
from ..lexjson import lex_json_closebrace
from ..lexjson import lex_json_openbracket
from ..lexjson import lex_json_closebracket
from ..lexjson import lex_json_comma
from ..lexjson import lex_json_colon
from ..lexjson import make_make_jsonreader


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


def make_struct_reader(dct):

    def struct_reader(text, i):
        items = {}

        i = lex_json_whitespace(text, i)
        i = lex_json_openbrace(text, i)

        while True:
            i = lex_json_whitespace(text, i)

            try:
                i = lex_json_closebrace(text, i)
                break
            except LexError:
                pass

            if items:
                i = lex_json_comma(text, i)
                i = lex_json_whitespace(text, i)

            kstart = i
            i, k = lex_json_string(text, i)
            reader = dct.get(k)
            if reader is None:
                raise ParseError('Parsing JSON struct', text, kstart, i, 'Invalid member: "%s"' %(k,))
            if k in items:
                raise ParseError('Parsing JSON struct', text, kstart, i, 'Duplicate member: "%s"' %(k,))

            i = lex_json_whitespace(text, i)
            i = lex_json_colon(text, i)
            i = lex_json_whitespace(text, i)

            vstart = i
            try:

                i, v = reader(text, i)
            except ParseError as e:
                raise ParseError('Parsing JSON struct', text, vstart, i, 'Failed to parse "%s" member' %(k,)) from e

            items[k] = v

        needkeys = set(dct.keys())
        havekeys = set(items.keys())
        if needkeys != havekeys:
            raise ParseError('Parsing JSON struct', text, start, i, 'Missing members: %s' %(', '.join(needkeys.difference(havekeys()))))

        return i, items

    return struct_reader


def make_option_reader(reader):
    def option_reader(text, i):
        try:
            i = lex_json_null(text, i)
            return i, None
        except LexError:
            pass
        return reader(text, i)
    return option_reader


def make_set_reader(reader):
    list_reader = make_list_reader(reader)
    def set_reader(text, i):
        i, lst = list_reader(text, i)
        return i, set(lst)
    return set_reader


def make_list_reader(reader):

    def list_reader(text, i):
        items = []

        i = lex_json_whitespace(text, i)
        i = lex_json_openbracket(text, i)
        i = lex_json_whitespace(text, i)

        while True:
            i = lex_json_whitespace(text, i)

            try:
                i = lex_json_closebracket(text, i)
                break
            except:
                pass

            if items:
                i = lex_json_comma(text, i)
                i = lex_json_whitespace(text, i)

            i, v = reader(text, i)
            items.append(v)

        return i, items

    return list_reader


def make_dict_reader(key_reader, val_reader):

    def dict_reader(text, i):
        items = {}

        i = lex_json_whitespace(text, i)
        i = lex_json_openbrace(text, i)

        while True:
            i = lex_json_whitespace(text, i)

            try:
                i = lex_json_closebrace(text, i)
                break
            except:
                pass

            if items:
                i = lex_json_comma(text, i)
                i = lex_json_whitespace(text, i)

            try:
                i, k = key_reader(text, i)
            except ParseError as e:
                raise ParseError('Cannot parse JSON dict key "%s"' %(k,)) from e

            i = lex_json_whitespace(text, i)
            i = lex_json_colon(text, i)
            i = lex_json_whitespace(text, i)

            try:
                i, v = val_reader(text, i)
            except ParseError as e:
                raise ParseError('Cannot parse JSON dict value "%s"' %(v,)) from e
            i = lex_json_whitespace(text, i)

            items[k] = v
        return i, items

    return dict_reader


def make_reader_from_spec(make_reader, spec, is_dict_key):
    typ = type(spec)

    if typ == Value:
        reader = make_reader(spec.primtype, is_dict_key)
        if reader is None:
            raise ValueError('There is no JSON reader for datatype "%s"' %(spec.primtype,))
        return reader

    elif typ == Struct:
        dct = {}
        for k, v in spec.childs.items():
            dct[k] = make_reader_from_spec(make_reader, v, False)
        return make_struct_reader(dct)

    elif typ == Option:
        subreader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_option_reader(subreader)

    elif typ == Set:
        subreader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_set_reader(subreader)

    elif typ == List:
        subreader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_list_reader(subreader)

    elif typ == Dict:
        if type(spec.childs['_key_']) != Value:
            raise ValueError('JSON does not support composite dictionary keys')

        key_reader = make_reader_from_spec(make_reader, spec.childs['_key_'], True)
        val_reader = make_reader_from_spec(make_reader, spec.childs['_val_'], False)
        return make_dict_reader(key_reader, val_reader)

    assert False  # missing case


def json2objects(schema, spec, text):
    if not isinstance(schema, Schema):
        raise TypeError()
    if not isinstance(text, str):
        raise TypeError()

    reader = make_reader_from_spec(make_make_jsonreader(schema), spec, False)

    i, objects = reader(text, 0)
    return objects
