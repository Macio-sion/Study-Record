"""通知公告 DAO"""
from app.model.notice import Notice
from app.dao.base_dao import BaseDAO


class NoticeDAO(BaseDAO[Notice]):
    def __init__(self):
        super().__init__(Notice)


notice_dao = NoticeDAO()
