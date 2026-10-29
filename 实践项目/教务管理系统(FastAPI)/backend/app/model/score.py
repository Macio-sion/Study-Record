from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    semester_id = Column(Integer, ForeignKey('semesters.id', ondelete='RESTRICT'), nullable=False)
    score = Column(DECIMAL(5, 1), nullable=False)
    status = Column(String(20), nullable=False, default='draft')
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='RESTRICT'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', 'semester_id', name='uk_student_course_semester'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    student = relationship('Student', back_populates='scores')
    course = relationship('Course', back_populates='scores')
    semester = relationship('Semester', back_populates='scores')
    score_logs = relationship('ScoreLog', back_populates='score')
