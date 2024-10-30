from model.book import *
from model.db import db
from system.error_code import ERROR_CODE
from util import common
from util.response import paginate_data
from model.user import User
from system.exceptions import ApplicationError


def get_list_books(pagination_param, filter_obj):
    try:
        course_db = db.session.query(Book)

        # Filter
        for k,v in filter_obj.items():
            if k == 'keyword':
                course_db = course_db.filter(Book.course_name.ilike(f'%{v}%'))
        
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



def create_book(data):
    try:
        # Lấy title và author_id từ data
        title = data.get('title')
        author_id = data.get('author_id')

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

def update_book(data, book_id):
    try:
        book = db.session.query(Book).filter(
            Book.id==book_id,
        ).first()
        if not book:
            return None, ERROR_CODE["BOOK_NOT_FOUND"]

        author_id = data.get('author_id')
        title = data.get('title');
        if author_id:
            author = db.session.query(User).get(author_id)
            if not author:
                return None, ERROR_CODE["AUTHOR_NOT_FOUND"]


        for k, v in data.items():
            setattr(book, k, v)
        db.session.commit()
        return book.serialize(), None
    except ApplicationError as err:
        common.push_log_to_sentry(message='Update course failed', extra_data={
            'payload': data,
            'book_id': book_id,
            'error': str(err)
        })
        return None, err
    
def delete_book(book_id):
    try:
        book_item = db.session.query(Book).filter_by( id=book_id).first()
        if not book_item:
            return None, ERROR_CODE["BOOK_NOT_FOUND"]
        db.session.delete(book_item)
        db.session.commit()
        return True, None
    except ApplicationError as err:
        common.push_log_to_sentry(message='Delete cart item failed', extra_data={
            'error': str(err)
        })
        return None, err
    
def get_book_by_id(book_id):
    book_item: Book = db.session.query(Book).get(book_id)
    if not book_item:
        return None, ERROR_CODE["BOOK_NOT_FOUND"]
    return book_item.serialize(), None