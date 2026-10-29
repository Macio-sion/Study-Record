from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_no = Column(String(20), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    college_id = Column(Integer, ForeignKey('colleges.id', ondelete='RESTRICT'), nullable=False)
    gender = Column(String(4), nullable=False)
    title = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    user = relationship('User')
    college = relationship('College', back_populates='teachers')
    courses = relationship('Course', back_populates='teacher')
    schedules = relationship('Schedule', back_populates='teacher')
    club = relationship('Club', back_populates='advisor')
