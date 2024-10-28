from operator import sub
from re import S
from tabnanny import check
from model.book import *
from model.db import db
from system.error_code import ERROR_CODE
from util import common

from util.response import paginate_data
from sqlalchemy import desc, func, and_, or_
from model.user import User
from system.exceptions import ApplicationError
# from model.user import UserRole
# from internal import order as order_lib
import math
from util.response import response_error
from datetime import timedelta
from services.automation import *
from collections import defaultdict



def get_list_books(pagination_param, filter_obj, sort_value, user_id = None):
    try:
        course_db = db.session.query(Book)

        # Filter
        for k,v in filter_obj.items():
            if k == 'keyword':
                course_db = course_db.filter(Book.course_name.ilike(f'%{v}%'))

        # if sort_value and sort_value.get('sort_by') in common.LIST_KEY_SORT_COURSE:
        #     field = sort_value['sort_by']
        #     if field == 'learners_count':
        #         learners_subquery = db.session.query(
        #                 CourseEnrollment.course_id, 
        #                 func.count(CourseEnrollment.student_id)\
        #                     .label('learners_count')
        #             ).group_by(CourseEnrollment.course_id).subquery()
        #         course_db = course_db.outerjoin(
        #                 learners_subquery, 
        #                 learners_subquery.c.course_id == Course.id
        #             )
        #         field = func.coalesce(learners_subquery.c.learners_count, 0)
        #     elif field == 'created_at':
        #         field = getattr(Course, field)

        #     if sort_value['sort_type'] == "-":
        #         course_db = course_db.order_by(field)
        #     else:  
        #         course_db = course_db.order_by(desc(field))
        # elif sort_value and (sort_value.get('sort_by') not in (None, '')
        #     and sort_value.get('sort_by') not in common.LIST_KEY_SORT_COURSE):
        #     return [], None, None
        
    except ApplicationError as err:
        common.push_log_to_sentry(message='Get list courses failed', extra_data={
            'payload': filter_obj,
            'error': str(err)
        })
        return None, None, err
    
    list_item, pagination = paginate_data(course_db, pagination_param["page"], pagination_param["limit"], pagination_param["get_all"])
    
    data = [item.serialize() for item in list_item]

    return {
        'books': data
        }, pagination, None



def create_book(data, user_id):
    try:
        # Lấy title và author_id từ data
        title = data.get('title')
        author_id = user_id

        # Kiểm tra dữ liệu đầu vào
        if not title:
            raise ValueError("Title is required")
        if not author_id:
            raise ValueError("Author ID is required")

        # Khởi tạo đối tượng Book
        book = Book(title=title, author_id=author_id)

        # Thêm vào session và commit
        db.session.add(book)
        db.session.commit()

        return book.serialize(), None

    except ApplicationError as err:
        # Log lỗi đặc biệt với ApplicationError
        common.push_log_to_sentry(
            message='Create book failed',
            extra_data={'payload': data, 'error': str(err)}
        )
        return None, err

    except Exception as err:
        # Xử lý các ngoại lệ chung
        db.session.rollback()  # Rollback nếu có lỗi xảy ra
        common.push_log_to_sentry(
            message='Unexpected error during book creation',
            extra_data={'payload': data, 'error': str(err)}
        )
        return None, err
