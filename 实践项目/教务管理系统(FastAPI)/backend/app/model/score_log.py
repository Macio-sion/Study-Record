from sqlalchemy import Column, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class ScoreLog(Base):
    __tablename__ = 'score_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    score_id = Column(Integer, ForeignKey('scores.id', ondelete='CASCADE'), nullable=False)
    old_score = Column(DECIMAL(5, 1), nullable=True)
    new_score = Column(DECIMAL(5, 1), nullable=True)
    operator_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    __table_args__ = ({'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'})
    score = relationship('Score', back_populates='score_logs')
