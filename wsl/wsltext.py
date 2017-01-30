import wsl


def make_make_wslreader(schema):
    if not isinstance(schema, wsl.Schema):
        raise ValueError()
    def make_wslreader(domain):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'decode'):
            return None
        if not hasattr(domobj.funcs, 'wsllex'):
            return None
        decode = domobj.funcs.decode
        wsllex = domobj.funcs.wsllex
        def wslreader(text, i):
            i, token = wsllex(text, i)
            return i, decode(token)
        return wslreader
    return make_wslreader


def make_make_wslwriter(schema):
    if not isinstance(schema, wsl.Schema):
        raise ValueError()
    def make_wslwriter(domain):
        domobj = schema.domains.get(domain)
        if domobj is None:
            return None
        if not hasattr(domobj.funcs, 'encode'):
            return None
        if not hasattr(domobj.funcs, 'wslunlex'):
            return None
        encode = domobj.funcs.encode
        wslunlex = domobj.funcs.wslunlex
        def wslwriter(value):
            return wslunlex(encode(value))
        return wslwriter
    return make_wslwriter
