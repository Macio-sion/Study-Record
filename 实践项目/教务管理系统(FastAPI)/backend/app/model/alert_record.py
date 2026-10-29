from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class AlertRecord(Base):
    __tablename__ = 'alert_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    semester_id = Column(Integer, ForeignKey('semesters.id', ondelete='RESTRICT'), nullable=False)
    alert_level = Column(String(20), nullable=False)
    alert_type = Column(String(50), nullable=True)
    description = Column(String(500), nullable=True)
    attendance_rate = Column(DECIMAL(5, 2), nullable=True)
    failed_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    handler_id = Column(Integer, nullable=True)
    handle_result = Column(String(500), nullable=True)
    handled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    student = relationship('Student', back_populates='alert_records')
    semester = relationship('Semester', back_populates='alert_records')
