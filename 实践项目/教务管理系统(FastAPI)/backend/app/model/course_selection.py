from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class CourseSelection(Base):
    __tablename__ = 'course_selections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    semester_id = Column(Integer, ForeignKey('semesters.id', ondelete='RESTRICT'), nullable=False)
    selected_at = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(String(10), nullable=False, default='selected')
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', 'semester_id', name='uk_student_course'),
        Index('idx_selection_student', 'student_id', 'semester_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    student = relationship('Student', back_populates='course_selections')
    course = relationship('Course', back_populates='course_selections')
    semester = relationship('Semester', back_populates='course_selections')
