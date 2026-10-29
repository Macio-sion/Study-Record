"""教室管理 Service"""
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.classroom_dao import classroom_dao
from app.model.classroom import Classroom
from app.dto.classroom_schema import ClassroomCreate, ClassroomUpdate, ClassroomResponse, ClassroomPageQuery
from app.common.exception import NotFoundException


async def create_classroom(db: AsyncSession, req: ClassroomCreate) -> ClassroomResponse:
    classroom = Classroom(room_no=req.room_no, name=req.name, building=req.building, capacity=req.capacity, type=req.type, status=req.status)
    classroom = await classroom_dao.create(db, classroom)
    return ClassroomResponse.model_validate(classroom)


async def update_classroom(db: AsyncSession, classroom_id: int, req: ClassroomUpdate) -> ClassroomResponse:
    classroom = await classroom_dao.get_by_id(db, classroom_id)
    if not classroom:
        raise NotFoundException(f"教室不存在: id={classroom_id}")
    classroom = await classroom_dao.update(db, classroom, name=req.name, building=req.building, capacity=req.capacity, type=req.type, status=req.status)
    return ClassroomResponse.model_validate(classroom)


async def delete_classroom(db: AsyncSession, classroom_id: int) -> bool:
    if not await classroom_dao.delete(db, classroom_id):
        raise NotFoundException(f"教室不存在: id={classroom_id}")
    return True


async def get_classroom(db: AsyncSession, classroom_id: int) -> ClassroomResponse:
    classroom = await classroom_dao.get_by_id(db, classroom_id)
    if not classroom:
        raise NotFoundException(f"教室不存在: id={classroom_id}")
    return ClassroomResponse.model_validate(classroom)


async def list_classrooms(db: AsyncSession, query: ClassroomPageQuery) -> tuple[list[ClassroomResponse], int]:
    filters = []
    if query.building:
        filters.append(Classroom.building == query.building)
    if query.type:
        filters.append(Classroom.type == query.type)
    if query.status:
        filters.append(Classroom.status == query.status)
    if query.keyword:
        filters.append(or_(Classroom.name.like(f"%{query.keyword}%"), Classroom.room_no.like(f"%{query.keyword}%")))
    items, total = await classroom_dao.get_all(db, page=query.page, page_size=query.page_size, filters=filters, order_by=Classroom.room_no)
    return [ClassroomResponse.model_validate(c) for c in items], total
