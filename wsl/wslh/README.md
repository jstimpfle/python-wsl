# WSL-H

This is a little language which enables the simultaneous description of an
hierarchical schema and how hierarchies can be queried from, or inserted into,
relational databases.

For better understanding start looking at tests.py and try to understand how it
converts between three different representations of data - relational database,
in-memory object hierarchy, and object hierarchy serialized as text - given a
relational schema and a hierarchical description.

WSL-H is developped for use with
[WSL](http://jstimpfle.de/projects/wsl/main.html) databases but it should be
trivial to use it with almost any relational database.
