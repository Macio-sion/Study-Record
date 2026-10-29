from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role_code = Column(String(20), nullable=False)
    real_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    managed_college_id = Column(Integer, ForeignKey('colleges.id', ondelete='SET NULL'), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (Index('idx_users_role', 'role_code'), {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    managed_college = relationship('College', foreign_keys=[managed_college_id])
