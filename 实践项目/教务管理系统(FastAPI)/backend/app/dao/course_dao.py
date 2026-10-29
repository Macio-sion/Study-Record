"""课程/学期 DAO"""
from app.model.course import Course
from app.model.semester import Semester
from app.dao.base_dao import BaseDAO


class SemesterDAO(BaseDAO[Semester]):
    def __init__(self):
        super().__init__(Semester)


class CourseDAO(BaseDAO[Course]):
    def __init__(self):
        super().__init__(Course)


semester_dao = SemesterDAO()
course_dao = CourseDAO()
