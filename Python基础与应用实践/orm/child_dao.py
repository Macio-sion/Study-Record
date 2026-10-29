"""
@Author : Administrator
@Company : 
@Date : 2026/7/25 9:32
@Desc :
@Version : 1.0
"""
from base import Base
from sqlalchemy import Column, String


class User(Base):
    __tablename__ = 'user'
    name = Column(String(50), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.name

