"""节点五（解析结果校验与补全）业务代码"""

import re


# 必填字段（点号路径）
REQUIRED_FIELDS = ["personal.name", "personal.phone"]

# 置信度阈值：低于此值进 pending
CONFIDENCE_THRESHOLD = 0.6

# 格式校验规则（字段名 → 正则）
_FORMAT_RULES = {
    "phone": re.compile(r"^1[3-9]\d{9}$"),
    "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    "birth_date": re.compile(r"^\d{4}-\d{2}(-\d{2})?$"),
    "start": re.compile(r"^\d{4}-\d{2}(-\d{2})?$"),
    "end": re.compile(r"^\d{4}-\d{2}(-\d{2})?$"),
}

# 日期字段允许的「进行中」等非日期取值
_DATE_OPEN_VALUES = ("至今", "现在", "present", "now")


def validate(fields: dict) -> tuple[dict, list]:
    """校验解析结果，返回 (校验报告, 待确认/待补充清单)"""
    report = {
        "total": 0,
        "filled": 0,
        "missing_required": [],
        "low_confidence": [],
        "format_invalid": [],
    }
    pending = []

    # 1. 必填字段缺失检测
    for path in REQUIRED_FIELDS:
        node = _get_by_path(fields, path)
        if node is None or node.get("value") is None:
            report["missing_required"].append(path)
            pending.append({"field": path, "reason": "缺失", "confidence": 0.0})

    # 2. 遍历所有字段：统计 + 置信度 + 格式
    for path, node in _walk_fields(fields):
        value = node.get("value")
        confidence = node.get("confidence", 0.0)
        report["total"] += 1
        if value is not None:
            report["filled"] += 1
        if value is None:
            continue

        # 置信度阈值检查
        if confidence < CONFIDENCE_THRESHOLD:
            report["low_confidence"].append(path)
            pending.append({"field": path, "reason": "低置信度", "confidence": confidence})

        # 格式合法性校验
        field_name = path.rsplit(".", 1)[-1]
        if not _format_valid(field_name, str(value)):
            report["format_invalid"].append(path)
            pending.append({"field": path, "reason": "格式非法", "confidence": confidence})

    return report, pending


def _format_valid(field_name: str, value: str) -> bool:
    """按字段名做格式校验，日期字段允许「至今」等非日期取值"""
    rule = _FORMAT_RULES.get(field_name)
    if rule is None:
        return True
    if field_name in ("start", "end") and value in _DATE_OPEN_VALUES:
        return True
    return bool(rule.match(value))


def _get_by_path(fields: dict, path: str):
    """按点号路径取字段节点"""
    node = fields
    for part in path.split("."):
        if isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


def _walk_fields(node, prefix: str = ""):
    """递归遍历字段，yield (path, node)，node 含 value/confidence"""
    if isinstance(node, dict):
        if "value" in node and "confidence" in node:
            yield prefix, node
        else:
            for key, val in node.items():
                path = f"{prefix}.{key}" if prefix else key
                yield from _walk_fields(val, path)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_fields(item, f"{prefix}[{i}]")
