class WslValueError(ValueError):
    """Base class for all WSL exceptions"""


class LexError(WslValueError):
    """Raised on WSL text format token lexing errors"""

    def __init__(self, domainname, text, startpos, errorpos, errormsg):

        assert isinstance(domainname, str)
        assert isinstance(text, str)
        assert isinstance(startpos, int)
        assert isinstance(errorpos, int)
        assert isinstance(errormsg, str)

        super()

        self.domainnname = domainname
        self.text = text
        self.startpos = startpos
        self.errorpos = errorpos
        self.errormsg = errormsg


class ParseError(WslValueError):
    """Raised on general parsing errors"""

    def __init__(self, context, text, startpos, errorpos, errormsg):

        assert isinstance(context, str)
        assert isinstance(text, str)
        assert isinstance(startpos, int)
        assert isinstance(errorpos, int)
        assert isinstance(errormsg, str)

        super()

        self.context = context
        self.text = text
        self.startpos = startpos
        self.errorpos = errorpos
        self.errormsg = errormsg


class FormatError(WslValueError):
    """Raised on database formatting errors"""


class IntegrityError(WslValueError):
    """Raised on database inconsistencies"""
