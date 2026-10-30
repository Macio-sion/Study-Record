"""节点（检索）业务代码：简历结构化字段展开为条目级检索块"""

from typing import List


def flatten_fields(fields: dict) -> List[dict]:
    """把结构化简历展开为条目级检索块（personal/summary 各一块，列表字段每条一块）"""
    if not fields:
        return []
    retrieved: List[dict] = []

    # 单对象：personal
    personal = fields.get("personal")
    if isinstance(personal, dict):
        text = _serialize_field_values(personal)
        if text:
            retrieved.append({"source": "resume", "field": "personal", "text": text, "score": 1.0})

    # 单对象：summary（FieldValue）
    summary = fields.get("summary")
    if isinstance(summary, dict) and summary.get("value") is not None:
        retrieved.append({"source": "resume", "field": "summary", "text": str(summary["value"]), "score": 1.0})

    # 列表对象：education/experience/skills/certificates/awards
    for list_key in ("education", "experience", "skills", "certificates", "awards"):
        items = fields.get(list_key) or []
        for i, item in enumerate(items):
            text = _serialize_field_values(item)
            if text:
                retrieved.append({"source": "resume", "field": f"{list_key}[{i}]", "text": text, "score": 1.0})

    # extra（结构特殊：{name, value, confidence}）
    for i, item in enumerate(fields.get("extra") or []):
        if isinstance(item, dict) and item.get("value") is not None:
            name = item.get("name") or f"extra[{i}]"
            retrieved.append({"source": "resume", "field": f"extra[{i}]", "text": f"{name}: {item['value']}", "score": 1.0})

    return retrieved


def _serialize_field_values(entry: dict) -> str:
    """把 {字段名: {value, confidence}} 序列化为可读文本"""
    parts = []
    for key, node in entry.items():
        if isinstance(node, dict) and node.get("value") is not None:
            parts.append(f"{key}: {node['value']}")
    return "; ".join(parts)
