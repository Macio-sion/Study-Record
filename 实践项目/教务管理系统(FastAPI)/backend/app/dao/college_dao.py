"""
学院/专业 DAO
"""
from app.model.college import College
from app.model.major import Major
from app.dao.base_dao import BaseDAO


class CollegeDAO(BaseDAO[College]):
    def __init__(self):
        super().__init__(College)


class MajorDAO(BaseDAO[Major]):
    def __init__(self):
        super().__init__(Major)


college_dao = CollegeDAO()
major_dao = MajorDAO()
