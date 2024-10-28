from flask import jsonify, Response, send_file


def response_list(data_list, offset=None, limit=None, count=None, extra_data=None):
    return jsonify({
        'items': data_list,
        'pagination': {
            'offset': offset,
            'limit': limit,
            'count': count,
        },
        'extra_data': extra_data
    }), 200


def response200(data):
    return jsonify({
        'success': True,
        'status': 200,
        'data': data
    }), 200

