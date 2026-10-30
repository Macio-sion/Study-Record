"""简历路由：上传 / 列表 / 详情 / 确认字段 / 版本管理 / 导出。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from api.deps import CurrentUser
from api.schemas import ConfirmFieldsRequest, ok
from db import repositories
from taskqueue.storage import store_file
from services.edit_engine.version import (
    next_version,
    set_field_value,
    version_store,
)

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(file: UploadFile, user_id: str = CurrentUser):
    """上传简历文件字节流，返回 file_id（解析任务用）。"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    file_id = store_file(data)
    return ok({"file_id": file_id, "file_name": file.filename or ""})


@router.get("")
def list_resumes(user_id: str = CurrentUser, page: int = 1, page_size: int = 10):
    return ok(repositories.list_resumes(user_id, page, page_size))


@router.get("/{resume_id}")
def get_resume(resume_id: str, user_id: str = CurrentUser):
    resume = repositories.get_resume_for_user(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    return ok(_resume_detail(resume))


@router.patch("/{resume_id}/fields")
def confirm_fields(resume_id: str, body: ConfirmFieldsRequest, user_id: str = CurrentUser):
    resume = repositories.get_resume_for_user(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    fields = resume["fields"] or {}
    for c in body.confirmations:
        set_field_value(fields, c.field, c.value)

    repositories.update_resume_fields(resume_id, fields, resume.get("pending") or [])
    # 同步写入版本快照（起始版本 v1 或覆盖当前最新）
    version_store.save(resume_id, "v1", fields, note="manual confirm")
    return ok(_resume_detail(repositories.get_resume(resume_id)))


# ---------------------------------------------------------------------------
# 版本管理
# ---------------------------------------------------------------------------

@router.get("/{resume_id}/versions")
def list_versions(resume_id: str, user_id: str = CurrentUser, page: int = 1, page_size: int = 20):
    _ensure_owner(resume_id, user_id)
    records = version_store.list(resume_id)
    total = len(records)
    start = (page - 1) * page_size
    return ok({"page": page, "page_size": page_size, "total": total, "list": records[start:start + page_size]})


@router.get("/{resume_id}/versions/{version}")
def get_version(resume_id: str, version: str, user_id: str = CurrentUser):
    _ensure_owner(resume_id, user_id)
    record = version_store.get(resume_id, version)
    if not record:
        raise HTTPException(status_code=404, detail="版本不存在")
    return ok(record)


@router.post("/{resume_id}/versions/rollback/{version}")
def rollback_version(resume_id: str, version: str, user_id: str = CurrentUser):
    _ensure_owner(resume_id, user_id)
    record = version_store.get(resume_id, version)
    if not record:
        raise HTTPException(status_code=404, detail="版本不存在")

    latest = version_store.latest(resume_id)
    new_version = next_version(latest["version"]) if latest else "v2"
    version_store.save(resume_id, new_version, record["fields"], note=f"rollback from {version}")
    repositories.update_resume_fields(resume_id, record["fields"], None)
    return ok({"version": new_version, "resume_id": resume_id})


@router.get("/{resume_id}/export")
def export_resume(resume_id: str, user_id: str = CurrentUser):
    resume = repositories.get_resume_for_user(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    return ok(_resume_detail(resume))


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _ensure_owner(resume_id: str, user_id: str) -> None:
    if not repositories.get_resume_for_user(resume_id, user_id):
        raise HTTPException(status_code=404, detail="简历不存在")


def _resume_detail(resume: dict) -> dict:
    return {
        "resume_id": resume["id"],
        "name": resume["name"],
        "source": {
            "type": resume["source_type"],
            "ocr_used": resume["ocr_used"],
            "file_type": resume["source_type"],
        },
        "fields": resume["fields"] or {},
        "pending": resume["pending"] or [],
        "file_valid": True,
        "created_at": str(resume["created_at"]) if resume.get("created_at") else None,
        "updated_at": str(resume["updated_at"]) if resume.get("updated_at") else None,
    }
