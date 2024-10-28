
def get_pagination_params(request):
    limit = int(request.args.get('limit', 10))
    page = int(request.args.get('page', 1))
    get_all = request.args.get('get_all', False)
    return {
        'limit': limit,
        'page': page,
        'get_all': get_all
    }

def get_sort_param(request):
    sort_param = request.args.get('sort', None)
    if sort_param is None or sort_param == '':
        return None
    sort_type = '-' if sort_param[0] == '-' else ''
    sort_by = sort_param.replace('-', '') if sort_param[0] == '-' else sort_param
    sort_dict = {
        'sort_type': sort_type,
        'sort_by': sort_by
    }
    return sort_dict

def comma_separated_list(value):
    return value.split(',')