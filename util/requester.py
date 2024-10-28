from dateutil.parser import parse
import hashlib
import hmac
import json

from system.exceptions import BadRequest
from system.exceptions import Unauthorized
from system.exceptions import UserInputInvalid

from util.dict import nested_get


def get_pagination_params(request):
    r_offset = request.args.get('offset', None, type=int)
    r_limit = request.args.get('limit', None, type=int)
    if r_offset is not None or r_limit is not None:
        return {
            'offset': r_offset or 0,
            'limit': r_limit,
        }

    r_start = request.args.get('_start', None, type=int)
    r_end = request.args.get('_end', None, type=int)
    offset = r_start
    limit = None
    if r_start is not None and r_end is not None:
        limit = r_end - r_start

    return {
        'offset': offset or 0,
        'limit': limit,
    }


def get_list_type_param(request, param_name):
    param = request.args.get(param_name, None)
    if param is not None:
        param = request.args.getlist(param_name)
    return param


def get_datetime_param_from_url(request, param_name, default_value):
    datetime_str = request.args.get(param_name, None)
    if datetime_str is None:
        return default_value

    try:
        return parse(datetime_str)
    except ValueError:
        raise BadRequest(f"'{param_name}' has an invalid format datetime")


def validate_header_x_hub(secret, headers, payload):
    try:
        header_x_hub_signature = headers['X-Hub-Signature'].split('=')[1]
        print(f'header_x_hub_signature: {header_x_hub_signature}')
        print(f'payload: {payload}')
        signature = hmac.new(bytes(secret, 'latin-1'), payload, hashlib.sha1).hexdigest()
        if not hmac.compare_digest(signature, header_x_hub_signature):
            raise Exception()
    except Exception as e:
        print(e)
        raise Unauthorized('Request header X-Hub-Signature not present or invalid')
