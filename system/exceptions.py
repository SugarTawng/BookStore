"""This module is for handle exception in this app

ApplicationError for generic application error
AssertionError for internal alert
"""
import logging
import traceback

import sentry_sdk
from werkzeug.exceptions import MethodNotAllowed
from flask import current_app as capp, jsonify
from voluptuous import Invalid as VoluptuousInvalid
from sqlalchemy.exc import SQLAlchemyError, DBAPIError, IntegrityError


class ApplicationError(Exception):
    def __init__(self, message="Application Error", code=400, detail=None, toraise=False):
        """toraise flag mean this exception should log to bug logging
        """
        Exception.__init__(self)
        self.message = message
        self.status_code = code
        self.detail = detail
        self.toraise = toraise


class Unauthorized(Exception):
    pass


class PermissionDenied(Exception):
    pass


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


class UserInputInvalid(Exception):
    pass


class SystemException(Exception):
    pass


class CustomException(Exception):
    pass


def make_error(message, detail=None, code=400):
    rv = {
        "success": False,
        "message": message,
    }
    if detail:
        rv["detail"] = detail
    return jsonify(rv), code

def database_rollback():
    try:
        capp.sess.rollback()
    except (SQLAlchemyError, DBAPIError):
        pass


def register_error_handlers(app):
    @app.errorhandler(Unauthorized)
    def handle_unauthorized(e):
        return make_error(f"Unauthorized: {str(e)}", code=401)

    @app.errorhandler(404)
    def handle_404(e):
        return make_error("API not Found", code=404)

    @app.errorhandler(MethodNotAllowed)
    def handle_405(e):
        return make_error("Method Not Allowed", code=405)

    @app.errorhandler(NotFound)
    def handle_not_found(e):
        return make_error(f"Not found: {str(e)}", code=404)

    @app.errorhandler(SystemException)
    def handle_system_exception(e):
        return make_error(f"SystemException: {e}", code=500)

    @app.errorhandler(PermissionDenied)
    def handle_permission_denied(e):
        return make_error(f"Permission Denied: {str(e)}", code=403)

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return make_error(f"{str(e)}", code=400)

    @app.errorhandler(UserInputInvalid)
    @app.errorhandler(VoluptuousInvalid)
    def handle_input_error(e):
        return make_error("Schema Invalid", detail=str(e), code=400)

    @app.errorhandler(IntegrityError)
    def handle_object_integrity(e):
        database_rollback()
        logging.error(traceback.format_exc())
        return make_error("Invalid Value: Object already exist or a reference mismatch", code=400)

    @app.errorhandler(DBAPIError)
    @app.errorhandler(SQLAlchemyError)
    def hande_database_error(e):
        database_rollback()
        sentry_sdk.capture_exception()
        logging.error(traceback.format_exc())
        return make_error("Database Error", detail=str(e), code=400)

    @app.errorhandler(ApplicationError)
    def handle_application_error(e):
        database_rollback()
        if e.toraise:
            sentry_sdk.capture_exception()
            logging.error(traceback.format_exc())
        return make_error("Application Error", detail=str(e), code=400)

    @app.errorhandler(CustomException)
    def handle_custom_error(e, code):
        return make_error(f"{str(e)}", code=code)

    @app.errorhandler(AssertionError)
    @app.errorhandler(Exception)
    def handle_all(e):
        database_rollback()
        sentry_sdk.capture_exception()
        logging.error(traceback.format_exc())
        return make_error("Unexpected Error", detail=e.__class__.__name__, code=400)
