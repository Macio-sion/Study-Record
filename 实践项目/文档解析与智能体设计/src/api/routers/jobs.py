"""求职记录路由：CRUD + 进度看板。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.deps import CurrentUser
from api.schemas import CreateJobRequest, UpdateJobRequest, ok
from db import repositories

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
def list_jobs(user_id: str = CurrentUser, status: str | None = None, page: int = 1, page_size: int = 10):
    return ok(repositories.list_jobs(user_id, status, page, page_size))


@router.post("")
def create_job(body: CreateJobRequest, user_id: str = CurrentUser):
    job = repositories.create_job(
        user_id, body.company, body.position, body.status, body.date, body.note
    )
    return ok(job)


@router.patch("/{job_id}")
def update_job(job_id: str, body: UpdateJobRequest, user_id: str = CurrentUser):
    _ensure_owner(job_id, user_id)
    job = repositories.update_job(
        job_id,
        company=body.company,
        position=body.position,
        status=body.status,
        date=body.date,
        note=body.note,
    )
    return ok(job)


@router.delete("/{job_id}")
def delete_job(job_id: str, user_id: str = CurrentUser):
    _ensure_owner(job_id, user_id)
    repositories.delete_job(job_id)
    return ok({"deleted": True})


@router.get("/board")
def board(user_id: str = CurrentUser):
    return ok({"board": repositories.job_board(user_id)})


def _ensure_owner(job_id: str, user_id: str) -> None:
    job = repositories.get_job(job_id)
    if not job or job["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="记录不存在")
