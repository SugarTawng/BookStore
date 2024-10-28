from model.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Book(db.Model):
    __tablename__ = "book"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), unique=True, nullable=False)
    author_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)

    author = relationship("User", back_populates="books")
    receipts = relationship("Receipt", back_populates="book")
    
    # Định nghĩa hàm serialize

    def serialize(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'author_id': str(self.author_id)
        }
    
