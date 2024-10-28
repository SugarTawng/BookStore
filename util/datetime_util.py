import datetime
import pytz


def get_now():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
