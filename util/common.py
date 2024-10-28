from datetime import date, timedelta
import json
from time import strptime
from unicodedata import category
import urllib.parse as urlparse
from sentry_sdk import capture_message, configure_scope
from operator import attrgetter

from sqlalchemy import false, true

LIST_KEY_SORT_FEED = ["created_at", "views_count"]
LIST_KEY_SORT_EVENT = ["created_at", "start_datetime", "end_datetime"]
LIST_KEY_SORT_HASHTAG = ["uses_count"]
LIST_KEY_SORT_CATEGORY = ["created_at", "type"]
LIST_KEY_SORT_INDUSTRY = ["created_at", "type"]
LIST_KEY_SORT_COURSE = ["created_at", "learners_count"]
LIST_KEY_SORT_EDUCATOR = ["courses_count"]
LIST_KEY_SORT_COURSE_REVIEW = ["created_at", "rating"]
LIST_KEY_SORT_NOTEBOOKS = ["created_at", "updated_at", "time_note"]
LIST_KEY_SORT_COURSE_TESTIMONIAL = ["created_at"]
LIST_KEY_SORT_USER = ["created_at", "date_of_birth"]
SUCCEEDED = "succeeded"
MESSAGE_REFUND_SUCCEEDED = "Your refund has been processed successfully"
MESSAGE_REFUND_FAILED = "Your refund failed"
CURRENCY = "sgd"
FAILED = "failed"
MAX_NUMBER_TABLE = 100
FRONTEND_URL = "https://edtronaut.ai"

def push_log_to_sentry(message, user=None, extra_data=None):
    with configure_scope() as scope:
        if user:
            scope.user = user
        if extra_data:
            scope.set_extra('payload', json.dumps(extra_data))
        capture_message(message, 'error')


def add_param_to_url(url, params):
    url_parse = urlparse.urlparse(url)
    query = url_parse.query
    url_dict = dict(urlparse.parse_qsl(query))
    url_dict.update(params)
    url_new_query = urlparse.urlencode(url_dict)
    url_parse = url_parse._replace(query=url_new_query)
    return urlparse.urlunparse(url_parse)


def sort_list_value(list_value, sort_value, white_list):
    if sort_value and sort_value.get('sort_by') in white_list:
        field = sort_value['sort_by']
        if field == "name" and sort_value['sort_type'] == "-":
            list_value.sort(key=lambda x: x.name.upper(), reverse=True)
        elif field == "name":
            list_value.sort(key=lambda x: x.name.upper())
        elif sort_value['sort_type'] == "-":
            list_value.sort(key=attrgetter(field), reverse=True)
        else:
            list_value.sort(key=attrgetter(field))
        return list_value
    elif sort_value and sort_value.get('sort_by') not in white_list:
        return []
    return list_value 

def get_date_default(report_interval):
    subtract_date = 6
    if report_interval == 'week':
        subtract_date *= 7
    if report_interval == 'month':
        subtract_date *= 30

    end_date = date.today()
    start_date = end_date - timedelta(subtract_date)

    return start_date, end_date        
