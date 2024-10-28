from model.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Receipt(db.Model):
    __tablename__ = "receipt"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    book_id = Column(Integer, ForeignKey("book.id"))

    # Thiết lập quan hệ N-N với User và Book
    user = relationship("User", back_populates="receipts")
    book = relationship("Book", back_populates="receipts")
