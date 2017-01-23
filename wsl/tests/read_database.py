import wsl

schema_string = """
DOMAIN ID ID
DOMAIN String String
TABLE Person ID String
"""

database_string = """
Person john [John Doe]
Person jane [Jane Dane]

Person max [Max Müller]

"""


schema = wsl.parse_schema(schema_string)

db = wsl.parse_db(schema=schema, dbstr=database_string)
