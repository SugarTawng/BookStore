from flask import jsonify
from flask_sqlalchemy import Pagination

def response_list(data_list, pagination):
    return jsonify({
        'success': 1,
        'data': data_list,
        'pagination': pagination,
    }), 200

def paginate_data(query, page, limit=10, get_all=False):
    total = query.count()
    if get_all:
        page = 1
        limit = total if total > 0 else 1
    
    items = query.limit(limit).offset((page - 1) * limit).all()
    pagination = Pagination(query, page=page, per_page=limit, total=total, items=items)

    data = pagination.items
    temp = total % limit
    total_page = pagination.pages
    # if temp > 0:
    #     total_page += 1
    return data, {
        "limit": limit,
        "page": page,
        'total_page': total_page,
        'count': total,
    }
    

def response200(data = dict()):
    return jsonify({
        'success': 1,
        'data': data
    }), 200

def response_error(message, detail=None, code=400):
    response = {
        "success": False,
        "message": str(message),
        "code": code
    }
    if detail:
        response["detail"] = detail
    return jsonify(response), code