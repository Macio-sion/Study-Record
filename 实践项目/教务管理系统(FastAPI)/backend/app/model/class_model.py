from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Class(Base):
    __tablename__ = 'classes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_no = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    major_id = Column(Integer, ForeignKey('majors.id', ondelete='RESTRICT'), nullable=False)
    advisor_id = Column(Integer, ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True)
    grade = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    major = relationship('Major', back_populates='classes')
    advisor = relationship('Teacher', foreign_keys=[advisor_id])
    students = relationship('Student', back_populates='class_')
