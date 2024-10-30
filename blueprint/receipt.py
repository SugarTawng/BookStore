from operator import is_
from token import OP
from click import Option
from flasgger.utils import swag_from
from flask import Blueprint, request
from requests import head
from util.response import response_list, response200, response_error
from voluptuous import Schema, Required, Optional, Coerce, All, validators, Range, In
from system.authentication_jwt import authorized
from internal import receipt
from model.receipt import *
from util.request import get_pagination_params, get_sort_param

bp = Blueprint("receipt", __name__, url_prefix="/api/receipts")

GET_LIST_RECEIPT = Schema({
    Optional('keyword'): str,
    Optional('sort'): str,
    Optional('limit'): Coerce(int),
    Optional('page'): Coerce(int),
})

@bp.route("/", methods=["GET"])
@authorized()
def get_list_receipt():
    filter_obj = GET_LIST_RECEIPT(request.args.to_dict())
    pagination = get_pagination_params(request)

    items, pagination, err = receipt.get_list_books(pagination, filter_obj)
    return err and response_error(err) or response_list(items, pagination)


CREATE_RECEIPT = Schema({
    Required('user_id'): validators.Coerce(uuid.UUID),
    Required('book_id'): validators.Coerce(uuid.UUID),
})


@bp.route("/", methods=["POST"])
@authorized()
def create_receipt():
    data = CREATE_RECEIPT(request.json)
    print('data: ', data)
    # create course
    receipt_item, err = receipt.create_receipt(data)
    return err and response_error(err) or response200(receipt_item)

UPDATE_RECEIPT_INFO = Schema({
    Required('book_id'): validators.Coerce(uuid.UUID),
})


@bp.route("/<uuid:user_id>/update/<uuid:book_id>", methods=["PATCH"])
@authorized()
def update_receipt(user_id,book_id):
    data = UPDATE_RECEIPT_INFO(request.json)
    receipt_item, err = receipt.update_receipt(user_id, book_id, data)
    return err and response_error(err) or response200(receipt_item)

@bp.route("/<uuid:user_id>/delete/<uuid:book_id>", methods=["DELETE"])
@authorized()
def delete_receipt(user_id, book_id):
    receipt_item, err = receipt.delete_receipt(user_id,book_id)
    return err and response_error(err) or response200(receipt_item)
