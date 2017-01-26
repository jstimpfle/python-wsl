import wsl
import wsl.wslh as wslh


myschema = wsl.parse_schema("""\
DOMAIN PID ID
DOMAIN CID ID
DOMAIN idx Int
DOMAIN String String
TABLE Person PID String String String
TABLE Course CID String
TABLE Lecturer CID idx PID
TABLE Tutor CID idx PID
REFERENCE LecturerCid Tutor cid * * => Course cid *
REFERENCE LecturerPid Tutor * * pid => Person pid * * *
REFERENCE TutorCid Tutor cid * * => Course cid *
REFERENCE TutorPid Tutor * * pid => Person pid * * *
""")

myspec = wslh.parse_spec(myschema, """\
Person: dict for (pid fn ln abbr) (Person pid fn ln abbr)
    _key_: value pid
    _val_: struct
        id: value pid
        firstname: value fn
        lastname: value ln
        abbr: value abbr
        lecturing: set for (cid X) (Lecturer cid X pid)
            _val_: value cid
        tutoring: set for (cid X) (Tutor cid X pid)
            _val_: value cid

Course: dict for (cid name) (Course cid name)
    _key_: value cid
    _val_: struct
        id: value cid
        name: value name
        lecturer: list for (idx pid) (Lecturer cid idx pid)
            _idx_: value idx
            _val_: value pid
        tutor: list for (idx pid) (Tutor cid idx pid)
            _idx_: value idx
            _val_: value pid

Tutor: set for (pid cid) (Tutor pid cid)
    _val_: struct
        person: value pid
        course: value cid

Lecturer: set for (pid cid) (Lecturer pid cid)
    _val_: struct
        person: value pid
        course: value cid
""")

print(myspec)
