"""课程与学期管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.semester_schema import SemesterCreate, SemesterUpdate
from app.dto.course_schema import CourseCreate, CourseUpdate, CoursePageQuery
from app.service import course_service

router = APIRouter(prefix="/api", tags=["课程与学期管理"])

# ========== 学期 ==========
@router.get("/semesters/all", summary="获取所有学期")
async def get_all_semesters(db: AsyncSession = Depends(get_db)):
    return success(data=await course_service.get_all_semesters(db))

@router.get("/semesters", summary="学期列表")
async def list_semesters(page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db)):
    items, total = await course_service.list_semesters(db, page, page_size)
    return success_page(items=items, total=total, page=page, page_size=page_size)

@router.post("/semesters", summary="创建学期", dependencies=[Depends(require_role("admin"))])
async def create_semester(req: SemesterCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await course_service.create_semester(db, req))

@router.put("/semesters/{semester_id}", summary="更新学期", dependencies=[Depends(require_role("admin"))])
async def update_semester(semester_id: int, req: SemesterUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await course_service.update_semester(db, semester_id, req))

# ========== 课程 ==========
@router.get("/courses", summary="课程列表")
async def list_courses(page: int = 1, page_size: int = 20, semester_id: int = None, college_id: int = None, teacher_id: int = None, type: str = None, category: str = None, keyword: str = None, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    # 学工自动过滤为本学院课程
    if current_user.role_code == 'academic_staff' and current_user.managed_college_id:
        college_id = current_user.managed_college_id
    query = CoursePageQuery(page=page, page_size=page_size, semester_id=semester_id, college_id=college_id, teacher_id=teacher_id, type=type, category=category, keyword=keyword)
    items, total = await course_service.list_courses(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)

@router.get("/courses/available", summary="学生可选课程列表")
async def get_available_courses(
    keyword: str = None,
    type: str = None,
    teacher_name: str = None,
    code: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学生浏览本学期可选课程（排除已选/已满），支持课程名、类型、教师名、编码筛选"""
    from app.service.student_service import get_student_by_user_id
    from app.service.course_service import list_available_courses
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    items = await list_available_courses(db, student.id, keyword=keyword, type=type, teacher_name=teacher_name, code=code)
    return success(data=items)


@router.get("/courses/my", summary="我的课程")
async def get_my_courses(
    semester_id: int = None,
    keyword: str = None,
    type: str = None,
    college_id: int = None,
    page: int = 1,
    page_size: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role_code == 'teacher':
        from app.service.teacher_service import get_teacher_by_user_id
        teacher = await get_teacher_by_user_id(db, current_user.id)
        if not teacher:
            raise HTTPException(status_code=404, detail="未找到关联的教师档案")
        query = CoursePageQuery(page=page, page_size=page_size, teacher_id=teacher.id,
                                semester_id=semester_id, keyword=keyword, type=type, college_id=college_id)
        items, total = await course_service.list_courses(db, query)
        return success_page(items=items, total=total, page=page, page_size=page_size)
    elif current_user.role_code == 'student':
        from app.service.student_service import get_student_by_user_id
        student = await get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=404, detail="未找到关联的学生档案")
        from app.service.selection_service import get_student_courses
        items = await get_student_courses(db, student.id, semester_id)
        return success(data=items)
    else:
        return success(data=[])


@router.get("/courses/{course_id}", summary="课程详情")
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await course_service.get_course(db, course_id))


@router.post("/courses", summary="创建课程", dependencies=[Depends(require_role("admin"))])
async def create_course(req: CourseCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await course_service.create_course(db, req))


@router.put("/courses/{course_id}", summary="更新课程", dependencies=[Depends(require_role("admin"))])
async def update_course(course_id: int, req: CourseUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await course_service.update_course(db, course_id, req))


@router.delete("/courses/{course_id}", summary="删除课程", dependencies=[Depends(require_role("admin"))])
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    await course_service.delete_course(db, course_id)
    return success(message="删除成功")
