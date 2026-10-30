import sys
import json
from pathlib import Path

# 项目根（config/prompts）与 src（state/services/llm/agent）都要在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.edit import info_collect
from services.edit_engine.version import (
    InMemoryVersionStore,
    apply_suggestions,
    diff_versions,
)

# 样例结构化简历字段（模拟解析引擎产出的 StructuredResume.fields）
FIELDS = {
    "personal": {"name": {"value": "张三", "confidence": 0.98}},
    "education": [
        {"school": {"value": "XX大学", "confidence": 0.95}, "major": {"value": "计算机", "confidence": 0.94}},
    ],
    "experience": [
        {
            "org": {"value": "XX公司", "confidence": 0.92},
            "role": {"value": "后端工程师", "confidence": 0.9},
            "description": {"value": "负责后端开发", "confidence": 0.88},
        },
    ],
    "skills": [{"name": {"value": "Python", "confidence": 0.9}}],
    "summary": {"value": "有后端开发经验", "confidence": 0.85},
}


def test_info_collect_empty():
    result = info_collect({})
    assert result["error_data"]["code"] == "EDIT_EMPTY_RESUME"
    print("[PASS] info_collect 空简历 → EDIT_EMPTY_RESUME")


def test_apply_and_diff():
    store = InMemoryVersionStore()
    suggestions = [
        {
            "id": "sug_1",
            "type": "STAR",
            "location": "experience[0].description",
            "before": "负责后端开发",
            "after": "主导XX系统从0到1搭建，接口响应时间降低40%",
            "explain": "补全 STAR 结果要素",
            "priority": "high",
        }
    ]
    result = apply_suggestions(store, "rsm_test", FIELDS, suggestions, ["sug_1"], accept_all=False)
    print("[PASS] apply 生成版本:", result["version"], "| 更新字段:", result["updated_fields"])
    assert result["version"] == "v2"
    assert result["updated_fields"] == ["experience[0].description"]

    diffs = diff_versions(store, "rsm_test", "v2")
    print("[PASS] diff 结果:", json.dumps(diffs, ensure_ascii=False))
    assert any(d["field"] == "experience[0].description" for d in diffs)


def test_accept_all():
    store = InMemoryVersionStore()
    suggestions = [
        {"id": "sug_1", "location": "experience[0].description", "before": "负责后端开发", "after": "优化后的描述A", "explain": "", "priority": "high"},
        {"id": "sug_2", "location": "summary", "before": "有后端开发经验", "after": "有2年后端开发经验", "explain": "", "priority": "medium"},
    ]
    result = apply_suggestions(store, "rsm_test", FIELDS, suggestions, [], accept_all=True)
    print("[PASS] accept_all 应用建议数:", len(result["updated_fields"]))
    assert len(result["updated_fields"]) == 2


if __name__ == "__main__":
    test_info_collect_empty()
    test_apply_and_diff()
    test_accept_all()
    print("\n全部确定性用例通过（生成/优化需本地 ollama，可参照 test_qa.py 联调）")
