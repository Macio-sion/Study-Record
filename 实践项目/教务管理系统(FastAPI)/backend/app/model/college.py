from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class College(Base):
    __tablename__ = 'colleges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    majors = relationship('Major', back_populates='college')
    teachers = relationship('Teacher', back_populates='college')
