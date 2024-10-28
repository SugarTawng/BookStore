import datetime
import uuid
import enum
from functools import wraps

def simple_serialize(rv):
    if not isinstance(rv, dict):
        raise ValueError

    for item in rv:
        if hasattr(rv[item], "to_json"):
            rv[item] = rv[item].to_json()
        elif isinstance(rv[item], datetime.datetime):
            rv[item] = rv[item].isoformat()
        elif isinstance(rv[item], uuid.UUID):
            rv[item] = str(rv[item])
        elif isinstance(rv[item], (int, float, bool, dict)):
            rv[item] = rv[item]
        elif isinstance(rv[item], enum.Enum) and hasattr(rv[item], "name"):
            rv[item] = rv[item].name
        elif rv[item] is None:
            continue
        else:
            rv[item] = str(rv[item])
    return rv

def make_simple_serialize(func):
    @wraps(func)
    def internal(*args, **kwargs):
        return simple_serialize(func(*args, **kwargs))
    return internal
