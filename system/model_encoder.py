import enum
import json
import uuid
from datetime import date, datetime

from sqlalchemy.ext.declarative import DeclarativeMeta
from werkzeug.http import http_date


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        encode_success, encoded_value = _encode_primary_value(obj)
        if encode_success:
            return encoded_value
        if isinstance(obj.__class__, DeclarativeMeta):
            fields = {}
            hidden = obj.__json_hidden__ or []
            valid_fields = []
            for x in dir(obj):
                if (
                    not x.startswith('_')
                    and x not in ['metadata']
                    and x not in hidden
                    and callable(obj.__getattribute__(x)) is False
                ):
                    valid_fields.append(x)

            for field in valid_fields:
                success, value = _encode_primary_value(obj.__getattribute__(field))
                fields[field] = value

            return fields
        return json.JSONEncoder.default(self, obj)


def _encode_primary_value(value):
    if isinstance(value, set):
        return True, list(value)
    if isinstance(value, datetime):
        return True, value.isoformat()
    if isinstance(value, date):
        return True, http_date(value.timetuple())
    if isinstance(value, uuid.UUID):
        return True, str(value)
    if isinstance(value, enum.Enum) and hasattr(value, "name"):
        return True, value.name
    try:
        json.dumps(value)
        return True, value
    except TypeError:
        return False, None
