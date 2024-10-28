import os
import datetime
import jwt, uuid
from functools import wraps
from flask import jsonify, request
from system.exceptions import ApplicationError, make_error, PermissionDenied, SystemException
from model.user import User
from model.model_enum import UserType

def authorized(role_string=None):
    def real_jwt_required(fn):
        @wraps(fn)
        def internal(*args, **kwargs):
            try:
                token = request.headers["Authorization"].split(" ")
                if len(token) != 2 or token[0] != "Bearer":
                    raise jwt.InvalidTokenError
                payload = jwt.decode(token[1], os.getenv("SECRET_KEY"), options={'verify_exp': False}, algorithms=["HS256"])
            except KeyError:
                return jsonify(
                    {"success": False, "message": "Authorization Header must be provide."}
                ), 401
            except jwt.ExpiredSignatureError:
                return jsonify(
                    {"success": False, "message": "Signature expired. Please log in again."}
                ), 401
            except jwt.InvalidTokenError:
                return jsonify(
                    {"success": False, "message": "Invalid token. Please check your token carefully or login again."}
                ), 401
            except ApplicationError as app_err:
                return make_error(app_err.message, detail=app_err.detail, code=403)
            try:
                request.user_id = uuid.UUID(payload["id"])
            except ValueError:
                return make_error("Invalid user id", code=403)
            
            return fn(*args, **kwargs)
        return internal
    return real_jwt_required


def encode_access_token(user_id) -> str:
    """
    Warn: user_id can be UUID so it need str(user_id)
    """
    payload = {
        "id": str(user_id),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")
