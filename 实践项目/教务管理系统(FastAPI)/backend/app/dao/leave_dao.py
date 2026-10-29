"""请假 DAO"""
from app.model.leave_request import LeaveRequest
from app.dao.base_dao import BaseDAO


class LeaveDAO(BaseDAO[LeaveRequest]):
    def __init__(self):
        super().__init__(LeaveRequest)


leave_dao = LeaveDAO()
