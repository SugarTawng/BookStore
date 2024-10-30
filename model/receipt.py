from model.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Receipt(db.Model):
    __tablename__ = "receipt"
    user_id = Column(Integer, ForeignKey("user.user_id"), primary_key=True, default=uuid.uuid4)
    book_id = Column(Integer, ForeignKey("book.id"), primary_key=True, default=uuid.uuid4)

    # Thiết lập quan hệ N-N với User và Book
    user = relationship("User", back_populates="receipts")
    book = relationship("Book", back_populates="receipts")

    def serialize(self):
        return {
            'book_id': self.book_id,
            'user_id': self.user_id
        }