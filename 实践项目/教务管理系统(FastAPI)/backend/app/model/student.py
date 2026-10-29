from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_no = Column(String(20), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    major_id = Column(Integer, ForeignKey('majors.id', ondelete='RESTRICT'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='RESTRICT'), nullable=False)
    gender = Column(String(4), nullable=False)
    enrollment_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    user = relationship('User')
    major = relationship('Major', back_populates='students')
    class_ = relationship('Class', back_populates='students')
    course_selections = relationship('CourseSelection', back_populates='student')
    attendances = relationship('Attendance', back_populates='student')
    scores = relationship('Score', back_populates='student')
    assignment_submissions = relationship('AssignmentSubmission', back_populates='student')
    leave_requests = relationship('LeaveRequest', back_populates='student')
    alert_records = relationship('AlertRecord', back_populates='student')
    club_members = relationship('ClubMember', back_populates='student')
