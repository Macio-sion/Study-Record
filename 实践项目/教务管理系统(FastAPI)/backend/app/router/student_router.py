"""学生与班级管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.student_schema import StudentCreate, StudentUpdate, StudentPageQuery
from app.dto.class_schema import ClassCreate, ClassUpdate, ClassPageQuery
from app.service import student_service

router = APIRouter(prefix="/api", tags=["学生与班级管理"])


async def _resolve_teacher_id(db, current_user):
    """教师角色：解析 teacher_id，非教师返回 None"""
    if current_user and current_user.role_code == "teacher":
        from app.service.teacher_service import get_teacher_by_user_id
        teacher = await get_teacher_by_user_id(db, current_user.id)
        if not teacher:
            raise HTTPException(status_code=404, detail="未找到关联的教师档案")
        return teacher.id
    return None


def _resolve_college_id(current_user):
    """学工角色：从 managed_college_id 获取管辖学院"""
    if current_user and current_user.role_code == "academic_staff":
        return current_user.managed_college_id
    return None


# ========== 班级 ==========
@router.get("/classes", summary="班级列表")
async def list_classes(
    page: int = 1, page_size: int = 20,
    college_id: int = None, major_id: int = None, grade: int = None, keyword: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    teacher_id = await _resolve_teacher_id(db, current_user)
    staff_college_id = _resolve_college_id(current_user)
    query = ClassPageQuery(page=page, page_size=page_size, college_id=college_id, major_id=major_id, grade=grade, keyword=keyword)
    items, total = await student_service.list_classes(db, query, teacher_id=teacher_id, college_id=staff_college_id)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@router.get("/classes/{class_id}", summary="班级详情")
async def get_class(class_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await student_service.get_class(db, class_id))

@router.post("/classes", summary="创建班级", dependencies=[Depends(require_role("admin"))])
async def create_class(req: ClassCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await student_service.create_class(db, req))

@router.put("/classes/{class_id}", summary="更新班级", dependencies=[Depends(require_role("admin"))])
async def update_class(class_id: int, req: ClassUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await student_service.update_class(db, class_id, req))

@router.delete("/classes/{class_id}", summary="删除班级", dependencies=[Depends(require_role("admin"))])
async def delete_class(class_id: int, db: AsyncSession = Depends(get_db)):
    await student_service.delete_class(db, class_id)
    return success(message="删除成功")

# ========== 学生 ==========
@router.get("/students", summary="学生列表")
async def list_students(
    page: int = 1, page_size: int = 20,
    college_id: int = None, class_id: int = None, major_id: int = None,
    enrollment_year: int = None, keyword: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    teacher_id = await _resolve_teacher_id(db, current_user)
    staff_college_id = _resolve_college_id(current_user)
    query = StudentPageQuery(page=page, page_size=page_size, college_id=college_id, class_id=class_id, major_id=major_id, enrollment_year=enrollment_year, keyword=keyword)
    items, total = await student_service.list_students(db, query, teacher_id=teacher_id, college_id=staff_college_id)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@router.get("/students/me", summary="获取当前学生档案")
async def get_my_student(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据当前登录用户的 user_id 获取学生档案"""
    from app.service.student_service import get_student_by_user_id
    from app.dto.student_schema import StudentResponse
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    return success(data=StudentResponse.model_validate(student))


@router.get("/students/{student_id}", summary="学生详情")
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await student_service.get_student(db, student_id))

@router.post("/students", summary="创建学生", dependencies=[Depends(require_role("admin"))])
async def create_student(req: StudentCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await student_service.create_student(db, req))

@router.put("/students/{student_id}", summary="更新学生", dependencies=[Depends(require_role("admin"))])
async def update_student(student_id: int, req: StudentUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await student_service.update_student(db, student_id, req))

@router.delete("/students/{student_id}", summary="删除学生", dependencies=[Depends(require_role("admin"))])
async def delete_student(student_id: int, db: AsyncSession = Depends(get_db)):
    await student_service.delete_student(db, student_id)
    return success(message="删除成功")
