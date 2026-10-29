"""教师 DAO"""
from app.model.teacher import Teacher
from app.dao.base_dao import BaseDAO


class TeacherDAO(BaseDAO[Teacher]):
    def __init__(self):
        super().__init__(Teacher)


teacher_dao = TeacherDAO()
