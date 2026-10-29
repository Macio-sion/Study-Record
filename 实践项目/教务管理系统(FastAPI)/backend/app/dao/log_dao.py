"""操作日志 DAO"""
from app.model.user_log import UserLog
from app.dao.base_dao import BaseDAO


class LogDAO(BaseDAO[UserLog]):
    def __init__(self):
        super().__init__(UserLog)


log_dao = LogDAO()
