from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.id', ondelete='RESTRICT'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='RESTRICT'), nullable=False)
    semester_id = Column(Integer, ForeignKey('semesters.id', ondelete='RESTRICT'), nullable=False)
    week_start = Column(Integer, nullable=False)
    week_end = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    period_start = Column(Integer, nullable=False)
    period_end = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = (
        UniqueConstraint('classroom_id', 'semester_id', 'week_start', 'day_of_week', 'period_start', name='uk_slot'),
        Index('idx_schedule_teacher_week', 'teacher_id', 'semester_id', 'week_start'),
        Index('idx_schedule_course', 'course_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    course = relationship('Course', back_populates='schedules')
    classroom = relationship('Classroom', back_populates='schedules')
    teacher = relationship('Teacher', back_populates='schedules')
    semester = relationship('Semester', back_populates='schedules')
