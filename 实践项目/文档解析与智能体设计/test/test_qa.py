import sys
import json
from pathlib import Path

# 项目根（config/prompts）与 src（state/services/llm/agent）都要在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.qa_graph import coaching_engine

# 样例结构化简历字段（模拟解析引擎产出的 StructuredResume.fields）
FIELDS = {
    "personal": {
        "name": {"value": "张三", "confidence": 0.98},
        "phone": {"value": "13812345678", "confidence": 0.97},
    },
    "education": [
        {"school": {"value": "XX大学", "confidence": 0.95}, "major": {"value": "计算机", "confidence": 0.94}},
    ],
    "experience": [
        {
            "org": {"value": "XX公司", "confidence": 0.92},
            "role": {"value": "后端工程师", "confidence": 0.9},
            "start": {"value": "2021-07", "confidence": 0.9},
            "end": {"value": "2024-06", "confidence": 0.9},
            "description": {"value": "负责XX系统后端开发，接口响应时间优化40%", "confidence": 0.88},
        },
    ],
    "skills": [
        {"name": {"value": "Python", "confidence": 0.9}},
        {"name": {"value": "Java", "confidence": 0.85}},
    ],
    "summary": {"value": "有2年后端开发经验，注重性能优化", "confidence": 0.85},
}


def main():
    question = "介绍你最有挑战的项目"
    result = coaching_engine.invoke({"question": question, "fields": FIELDS})

    print("=" * 70)
    print("面试辅导链路结果：")
    print("=" * 70)
    print("intent      :", result.get("intent"), "| confidence:", result.get("intent_confidence"))
    print("retrieved 数量:", len(result.get("retrieved", [])))
    print("retrieved来源:", [x["source"] for x in result.get("retrieved", [])])
    print("-" * 70)
    print("answer      :", result.get("answer"))
    print("citations   :", result.get("citations"))
    print("-" * 70)
    print("session_id  :", result.get("session_id"))
    print("history     :", json.dumps(result.get("history", []), ensure_ascii=False))


if __name__ == "__main__":
    main()
