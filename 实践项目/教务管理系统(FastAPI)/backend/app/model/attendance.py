from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Attendance(Base):
    __tablename__ = 'attendances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='RESTRICT'), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (
        UniqueConstraint('course_id', 'student_id', 'date', name='uk_course_student_date'),
        Index('idx_attendance_student', 'student_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    course = relationship('Course', back_populates='attendances')
    student = relationship('Student', back_populates='attendances')
