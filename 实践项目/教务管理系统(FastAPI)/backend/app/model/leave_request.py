from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    leave_type = Column(String(20), nullable=False)
    leave_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending_teacher')
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True)
    teacher_opinion = Column(String(200), nullable=True)
    teacher_at = Column(DateTime, nullable=True)
    staff_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    staff_opinion = Column(String(200), nullable=True)
    staff_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    student = relationship('Student', back_populates='leave_requests')
    course = relationship('Course', back_populates='leave_requests')
