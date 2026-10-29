from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Club(Base):
    __tablename__ = 'clubs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    advisor_id = Column(Integer, ForeignKey('teachers.id', ondelete='RESTRICT'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    advisor = relationship('Teacher', back_populates='club')
    members = relationship('ClubMember', back_populates='club')
