from flask import Blueprint, request, jsonify
from voluptuous import (
    REMOVE_EXTRA,
    Required,
    Schema,
    Optional,
    validators,
    Coerce,
)
from flasgger.utils import swag_from
from blueprint import auth
from system.authentication_jwt import authorized
from util.response import response200, response_error, response_list
import uuid, os, random, string
from system.exceptions import ApplicationError
from util.request import get_pagination_params, get_sort_param
from internal import user as user_lib


document_path = "../apidocs/apis/user"

bp = Blueprint("user", __name__, url_prefix="/api/users")

GET_LIST_USERS = Schema(
    {
        Optional("keyword"): str,
        Optional("sort"): str,
        Optional("limit"): Coerce(int),
        Optional("page"): Coerce(int),
    }
)

# Xong
@bp.route("/", methods=["GET"])
@swag_from(f"""{document_path}/get_list_users.yml""")
def get_list_users():
    filter_obj = GET_LIST_USERS(request.args.to_dict())
    pagination = get_pagination_params(request)
    sort_value = get_sort_param(request)
    items, pagination, err = user_lib.get_list_users(pagination, filter_obj, sort_value)
    return err and response_error(err) or response_list(items, pagination)

# Xong
@bp.route("/<uuid:user_id>", methods=["GET"])
@swag_from(f"""{document_path}/get_user_by_id.yml""")
def get_user_by_id(user_id):
    print("user id: ", user_id)
    user, err = user_lib.get_user_by_id(user_id)
    return err and response_error(err) or response200(user)


# @bp.route("/<uuid:followee_id>/check-follow", methods=["GET"])
# @authorized()
# @swag_from(f"""{document_path}/check_follow.yml""")
# def check_follow(followee_id):
#     data, err = user_lib.check_follow(request.user_id, followee_id)
#     return err and response_error(err) or response200(data)


# @bp.route("/<uuid:followee_id>/follows", methods=["POST"])
# @authorized()
# @swag_from(f"""{document_path}/follow_user.yml""")
# def follow_user(followee_id):
#     data, err = user_lib.follow_user(request.user_id, followee_id)
#     return err and response_error(err) or response200(data)
