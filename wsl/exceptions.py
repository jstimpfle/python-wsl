class WslError(Exception):
    """Base class for all WSL exceptions"""

class ParseError(WslError):
    """Raised on database parsing errors"""

class FormatError(WslError):
    """Raised on database formatting errors"""

class IntegrityError(WslError):
    """Raised on database inconsistencies"""
