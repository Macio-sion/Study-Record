from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class AssignmentSubmission(Base):
    __tablename__ = 'assignment_submissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    score = Column(DECIMAL(5, 1), nullable=True)
    comment = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, nullable=False, default=datetime.now)
    reviewed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='submitted', comment='submitted/reviewed')
    __table_args__ = (
        UniqueConstraint('assignment_id', 'student_id', name='uk_assignment_student'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    assignment = relationship('Assignment', back_populates='submissions')
    student = relationship('Student', back_populates='assignment_submissions')
