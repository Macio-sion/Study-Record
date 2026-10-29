from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Notice(Base):
    __tablename__ = 'notices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    publisher_id = Column(Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    target_role = Column(String(20), nullable=False, default='all')   # all / teacher / student
    college_id = Column(Integer, ForeignKey('colleges.id', ondelete='SET NULL'), nullable=True)
    major_id = Column(Integer, ForeignKey('majors.id', ondelete='SET NULL'), nullable=True)
    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    publisher = relationship('User')
    college = relationship('College')
    major = relationship('Major')
