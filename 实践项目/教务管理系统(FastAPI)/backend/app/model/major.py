from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Major(Base):
    __tablename__ = 'majors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    college_id = Column(Integer, ForeignKey('colleges.id', ondelete='RESTRICT'), nullable=False)
    duration = Column(Integer, nullable=False, default=4)
    degree = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    college = relationship('College', back_populates='majors')
    classes = relationship('Class', back_populates='major')
    students = relationship('Student', back_populates='major')
