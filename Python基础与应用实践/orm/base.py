"""
@Author : Administrator
@Company : 
@Date : 2026/7/25 9:27
@Desc :
@Version : 1.0
"""
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import Column, Integer, String, DATETIME, Boolean


class Base(DeclarativeBase):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    create_time = Column(DATETIME, default=datetime.now)
    update_time = Column(DATETIME, default=datetime.now)
    is_del = Column(Boolean, default=False)

