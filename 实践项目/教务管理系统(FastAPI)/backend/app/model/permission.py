from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.model.base import Base
from datetime import datetime

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    # relationships
    role_permissions = relationship('RolePermission', back_populates='permission')
