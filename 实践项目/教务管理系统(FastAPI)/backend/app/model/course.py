from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    semester_id = Column(Integer, ForeignKey('semesters.id', ondelete='RESTRICT'), nullable=False)
    college_id = Column(Integer, ForeignKey('colleges.id', ondelete='RESTRICT'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='RESTRICT'), nullable=False)
    credit = Column(DECIMAL(3, 1), nullable=False)
    max_capacity = Column(Integer, nullable=False)
    selected_count = Column(Integer, nullable=False, default=0)
    hours = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    category = Column(String(30), nullable=False, default='', server_default='')
    description = Column(String(500), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = (Index('idx_course_semester', 'semester_id'), Index('idx_course_teacher', 'teacher_id'), {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    semester = relationship('Semester', back_populates='courses')
    teacher = relationship('Teacher', back_populates='courses')
    schedules = relationship('Schedule', back_populates='course')
    course_selections = relationship('CourseSelection', back_populates='course')
    attendances = relationship('Attendance', back_populates='course')
    scores = relationship('Score', back_populates='course')
    assignments = relationship('Assignment', back_populates='course')
    leave_requests = relationship('LeaveRequest', back_populates='course')
