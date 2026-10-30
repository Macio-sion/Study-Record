"""简历智能生成与优化模块节点函数：信息获取 → 生成/逐条优化 → 一键应用与对比"""

import uuid

from state.edit_state import EditState
from services.edit_engine.skills import (
    ALL_OPTIMIZE_TYPES,
    generate_resume,
    normalize_fields,
    optimize_skills,
)
from services.edit_engine.version import (
    apply_suggestions,
    diff_versions,
    version_store,
)


def _new_resume_id() -> str:
    return f"rsm_{uuid.uuid4().hex[:8]}"


def info_collect(state: EditState) -> dict:
    """节点一：信息获取——统一简历数据来源（复用 StructuredResume 或手动输入）"""
    fields = state.get("fields")
    manual = state.get("manual_input")
    if not fields and not manual:
        return {"error_data": {
            "code": "EDIT_EMPTY_RESUME",
            "module": "info_collect",
            "message": "简历内容为空或信息严重不足，请先上传解析简历或手动输入",
            "place": "fields",
        }}

    resume_data = normalize_fields(fields or manual or {})
    return {
        "resume_data": resume_data,
        "resume_id": state.get("resume_id") or _new_resume_id(),
        "context_ready": True,
    }


def generate(state: EditState) -> dict:
    """节点二（简历生成）：SKILL-1 依据输入生成整份简历"""
    resume_data = state.get("resume_data") or {}
    return generate_resume(resume_data)


def optimize(state: EditState) -> dict:
    """节点二（逐条优化）：按优化类型串行执行各 SKILL，产出 EditSuggestion[]"""
    resume_data = state.get("resume_data") or {}
    jd = state.get("jd") or ""
    optimize_types = state.get("optimize_types") or ALL_OPTIMIZE_TYPES
    suggestions = optimize_skills(resume_data, jd, optimize_types)
    return {"suggestions": suggestions}


def apply(state: EditState) -> dict:
    """节点三：一键应用——应用建议生成新版本"""
    resume_id = state.get("resume_id") or "rsm_default"
    resume_data = state.get("resume_data") or {}
    suggestions = state.get("suggestions") or []
    if not suggestions:
        return {"error_data": {
            "code": "EDIT_NO_SUGGESTION",
            "module": "apply",
            "message": "没有可应用的优化建议，请先生成优化建议",
            "place": "suggestions",
        }}

    return apply_suggestions(
        version_store,
        resume_id,
        resume_data,
        suggestions,
        state.get("suggestion_ids") or [],
        state.get("accept_all", False),
    )


def diff(state: EditState) -> dict:
    """节点三：版本对比"""
    resume_id = state.get("resume_id") or "rsm_default"
    version = state.get("version")
    if not version:
        return {"error_data": {
            "code": "EDIT_NO_VERSION",
            "module": "diff",
            "message": "请指定要对比的版本号",
            "place": "version",
        }}

    return {"diffs": diff_versions(version_store, resume_id, version, state.get("base_version"))}


def should_continue(state: EditState) -> str:
    """交接模式：检查节点是否出错，有错则中断流水线"""
    if state.get("error_data"):
        return "end"
    return "continue"
