from operator import is_
from token import OP
from click import Option
from flasgger.utils import swag_from
from flask import Blueprint, request
from requests import head
from util.response import response_list, response200, response_error
from voluptuous import Schema, Required, Optional, Coerce, All, validators, Range, In
from system.authentication_jwt import authorized
from internal import book
from model.book import *
from util.request import get_pagination_params, get_sort_param

document_path = '../apidocs/apis/auth'

bp = Blueprint("book", __name__, url_prefix="/api/books")

GET_LIST_BOOKS = Schema({
    Optional('keyword'): str,
    Optional('sort'): str,
    Optional('limit'): Coerce(int),
    Optional('page'): Coerce(int),
})

@bp.route("/", methods=["GET"])
@authorized()
def get_list_books():
    filter_obj = GET_LIST_BOOKS(request.args.to_dict())
    pagination = get_pagination_params(request)

    items, pagination, err = book.get_list_books(pagination, filter_obj)
    return err and response_error(err) or response_list(items, pagination)

CREATE_BOOK = Schema({
    Required('title'): str,
    Optional('author_id'): validators.Coerce(uuid.UUID),
})


@bp.route("/", methods=["POST"])
@authorized()
def create_books():
    data = CREATE_BOOK(request.json)
    # create course
    course, err = book.create_book(data)
    return err and response_error(err) or response200(course)

UPDATE_BOOK_INFO = Schema({
    Optional('title'): str,
    Optional('author_id'): validators.Coerce(uuid.UUID),
    
})

@bp.route("/<uuid:book_id>", methods=["PATCH"])
@authorized()
def update_book(book_id):
    data = UPDATE_BOOK_INFO(request.json)
    book_item, err = book.update_book(data, book_id)
    return err and response_error(err) or response200(book_item)

@bp.route("/<uuid:book_id>", methods=["DELETE"])
@authorized()
def delete_book(book_id):
    book_item, err = book.delete_book(book_id)
    return err and response_error(err) or response200(book_item)

@bp.route("/<uuid:book_id>", methods=["GET"])
def get_book_by_id(book_id):
    user, err = book.get_book_by_id(book_id)
    return err and response_error(err) or response200(user)