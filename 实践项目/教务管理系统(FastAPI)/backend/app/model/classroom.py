from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Classroom(Base):
    __tablename__ = 'classrooms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_no = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    building = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    status = Column(String(10), nullable=False, default='available')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    schedules = relationship('Schedule', back_populates='classroom')
