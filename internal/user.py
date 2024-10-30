from model import User
from model.db import db
from system.error_code import ERROR_CODE
from system.exceptions import ApplicationError
from util import common
from sqlalchemy import desc
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
