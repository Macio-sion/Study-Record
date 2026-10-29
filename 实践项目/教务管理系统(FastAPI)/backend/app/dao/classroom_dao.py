"""教室 DAO"""
from app.model.classroom import Classroom
from app.dao.base_dao import BaseDAO


class ClassroomDAO(BaseDAO[Classroom]):
    def __init__(self):
        super().__init__(Classroom)


classroom_dao = ClassroomDAO()
