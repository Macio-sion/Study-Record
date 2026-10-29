from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Semester(Base):
    __tablename__ = 'semesters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    courses = relationship('Course', back_populates='semester')
    schedules = relationship('Schedule', back_populates='semester')
    course_selections = relationship('CourseSelection', back_populates='semester')
    scores = relationship('Score', back_populates='semester')
    alert_records = relationship('AlertRecord', back_populates='semester')
