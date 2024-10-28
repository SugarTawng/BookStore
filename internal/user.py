from datetime import datetime
from typing import Any
from model import User, Skill
from model.db import db
# from model.user import UserFollower
from system.authentication_jwt import encode_access_token
from system.error_code import ERROR_CODE
from system.exceptions import ApplicationError
from util import common
from sqlalchemy import desc, func
# from services.mail import mail_service
import time, jwt, os

from util.response import paginate_data


def get_list_users(
    pagination_param, filter_obj, sort_value
) -> tuple[list, None] | tuple[None, ApplicationError] | tuple[None, str]:
    try:
        user_db = db.session.query(User)

        # Filter
        for k, v in filter_obj.items():
            if k == "keyword":
                user_db = user_db.filter(User.email.ilike(f"%{v}%"))

        if sort_value and sort_value.get("sort_by") in common.LIST_KEY_SORT_USER:
            field = sort_value["sort_by"]
            field = getattr(User, field)

            if sort_value["sort_type"] == "-":
                User_db = User_db.order_by(field)
            else:
                User_db = User_db.order_by(desc(field))
        elif sort_value and (
            sort_value.get("sort_by") not in (None, "")
            and sort_value.get("sort_by") not in common.LIST_KEY_SORT_USER
        ):
            return [], None
    except ApplicationError as err:
        common.push_log_to_sentry(
            message="Get list users failed",
            extra_data={"payload": filter_obj, "error": str(err)},
        )
        return None, err
    items, pagination = paginate_data(
        user_db,
        pagination_param["page"],
        pagination_param["limit"],
        pagination_param["get_all"],
    )
    data = [item.list_serialize() for item in items]
    return {"users": data}, pagination, None


def get_user_by_id(user_id):
    user: User = db.session.query(User).get(user_id)
    if not user:
        return None, ERROR_CODE["USER_NOT_FOUND"]
    return user.simplified_serialize(), None

# def check_follow(user_id, followee_id):
#     is_following = db.session.query(UserFollower).filter(
#         UserFollower.user_id == followee_id, 
#         UserFollower.follower_id == user_id
#     ).first()
#     if not is_following:
#         return False, None

#     return True, None

# def follow_user(user_id, followee_id):
#     if user_id == followee_id:
#         return None, ERROR_CODE["NOT_ALLOW"]
#     followee: User = db.session.query(User).get(followee_id)
#     if not followee:
#         return None, ERROR_CODE["USER_NOT_FOUND"]

#     is_following = db.session.query(UserFollower).filter(
#         UserFollower.user_id == followee_id, 
#         UserFollower.follower_id == user_id
#     ).first()
#     if is_following:
#         db.session.delete(is_following)
#         db.session.commit()
#         return None, None

#     following = UserFollower(
#         user_id=followee_id,
#         follower_id=user_id,
#     )
#     db.session.add(following)
#     db.session.commit()

#     return following.serialize(), None
