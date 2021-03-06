import wsl

schema_string = """
DOMAIN ID ID
DOMAIN String String
TABLE Person ID String
REFERENCE Person Person a b => Person a b
"""

database_string = """
Person jane [Jane Dane]
Person john [John Doe]

Person max [Max Müller]

"""


schema = wsl.parse_schema(schema_string)

_, tables = wsl.parse_db(schema=schema, dbstr=database_string)

text = wsl.format_db(schema, tables, False)

_, tables2 = wsl.parse_db(schema=schema, dbstr=text)

assert tables == tables2
