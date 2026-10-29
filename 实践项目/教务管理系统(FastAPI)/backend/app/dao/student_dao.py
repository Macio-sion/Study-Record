"""学生/班级 DAO"""
from app.model.student import Student
from app.model.class_model import Class
from app.dao.base_dao import BaseDAO


class StudentDAO(BaseDAO[Student]):
    def __init__(self):
        super().__init__(Student)


class ClassDAO(BaseDAO[Class]):
    def __init__(self):
        super().__init__(Class)


student_dao = StudentDAO()
class_dao = ClassDAO()
