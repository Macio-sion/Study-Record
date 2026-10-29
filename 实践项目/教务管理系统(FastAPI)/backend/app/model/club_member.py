from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class ClubMember(Base):
    __tablename__ = 'club_members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(Integer, ForeignKey('clubs.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False, default='member')
    status = Column(String(20), nullable=False, default='approved', comment='pending/approved/rejected')
    joined_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = (
        UniqueConstraint('club_id', 'student_id', name='uk_club_student'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    club = relationship('Club', back_populates='members')
    student = relationship('Student', back_populates='club_members')
