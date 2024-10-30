from model.receipt import *
from model.db import db
from system.error_code import ERROR_CODE
from util import common
from util.response import paginate_data
from model.user import User
from system.exceptions import ApplicationError


def get_list_books(pagination_param, filter_obj):
    try:
        course_db = db.session.query(Receipt)

        # Filter
        for k,v in filter_obj.items():
            if k == 'keyword':
                course_db = course_db.filter(Receipt.course_name.ilike(f'%{v}%'))
        
    except ApplicationError as err:
        common.push_log_to_sentry(message='Get list courses failed', extra_data={
            'payload': filter_obj,
            'error': str(err)
        })
        return None, None, err
    
    list_item, pagination = paginate_data(course_db, pagination_param["page"], pagination_param["limit"], pagination_param["get_all"])
    
    data = [item.serialize() for item in list_item]

    return {
        'receipt': data
        }, pagination, None

def create_receipt(data):
    try:
        # Lấy book_id và user_id từ data
        book_id = data.get('book_id')
        user_id = data.get('user_id')

        print('book_id', book_id)
        print('user_id', user_id)

        # Kiểm tra dữ liệu đầu vào
        if not book_id:
            raise ValueError("Book ID is required")
        if not user_id:
            raise ValueError("User ID is required")

        # Kiểm tra xem Receipt đã tồn tại chưa
        existing_receipt = Receipt.query.filter_by(book_id=book_id, user_id=user_id).first()
        if existing_receipt:
            raise ValueError("Receipt with this User ID and Book ID already exists")

        # Khởi tạo đối tượng Receipt
        receipt = Receipt(book_id=book_id, user_id=user_id)

        # Thêm vào session và commit
        db.session.add(receipt)
        db.session.commit()

        return receipt.serialize(), None

    except ValueError as err:
        # Xử lý lỗi do người dùng cung cấp dữ liệu không hợp lệ
        return None, str(err)

    except ApplicationError as err:
        # Log lỗi đặc biệt với ApplicationError
        common.push_log_to_sentry(
            message='Create receipt failed',
            extra_data={'payload': data, 'error': str(err)}
        )
        return None, err

    except Exception as err:
        # Xử lý các ngoại lệ chung và rollback session
        db.session.rollback()
        common.push_log_to_sentry(
            message='Unexpected error during receipt creation',
            extra_data={'payload': data, 'error': str(err)}
        )
        return None, err


def delete_receipt(user_id, book_id):
    try:
        # Kiểm tra dữ liệu đầu vào
        if not book_id:
            raise ValueError("Book ID is required")
        if not user_id:
            raise ValueError("User ID is required")
        
        # Tìm Receipt cần xóa
        receipt = Receipt.query.filter_by(book_id=book_id, user_id=user_id).first()

        # Kiểm tra xem Receipt có tồn tại không
        if not receipt:
            raise ValueError("Receipt with this User ID and Book ID does not exist")

        # Xóa Receipt khỏi session và commit thay đổi
        db.session.delete(receipt)
        db.session.commit()

        return {"message": "Receipt deleted successfully"}, None

    except ValueError as err:
        # Xử lý lỗi nếu không tìm thấy Receipt
        return None, str(err)

    except Exception as err:
        # Rollback nếu có lỗi và log ngoại lệ
        db.session.rollback()
        common.push_log_to_sentry(
            message='Unexpected error during receipt deletion',
            extra_data={'book_id': book_id, 'user_id': user_id, 'error': str(err)}
        )
        return None, err

def update_receipt(user_id, book_id, data):
    try:
        if not book_id:
            raise ValueError("Book ID is required")
        if not user_id:
            raise ValueError("User ID is required")

        # Tìm Receipt cần cập nhật
        receipt = Receipt.query.filter_by(book_id=book_id, user_id=user_id).first()

        # Kiểm tra xem Receipt có tồn tại không
        if not receipt:
            raise ValueError("Receipt with this User ID and Book ID does not exist")

        new_book_id = data.get('book_id');
        
        if new_book_id:
            receipt.book_id = new_book_id

        # Commit thay đổi vào cơ sở dữ liệu
        db.session.commit()

        return {"message": "Receipt updated successfully", "receipt": receipt.serialize()}, None

    except ValueError as err:
        # Xử lý lỗi nếu không tìm thấy Receipt hoặc không có dữ liệu để cập nhật
        return None, str(err)

    except Exception as err:
        # Rollback nếu có lỗi và log ngoại lệ
        db.session.rollback()
        common.push_log_to_sentry(
            message='Unexpected error during receipt update',
            extra_data={'book_id': book_id, 'user_id': user_id, 'error': str(err)}
        )
        return None, str(err)