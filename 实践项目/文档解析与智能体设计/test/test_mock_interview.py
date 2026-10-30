import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.qa_graph import mock_interview_engine, qa_engine

FIELDS = {
    "personal": {"name": {"value": "张三", "confidence": 0.98}},
    "experience": [
        {
            "org": {"value": "XX公司", "confidence": 0.92},
            "role": {"value": "后端工程师", "confidence": 0.9},
            "description": {"value": "负责XX系统后端开发，接口响应时间优化40%", "confidence": 0.88},
        },
    ],
    "skills": [{"name": {"value": "Python", "confidence": 0.9}}],
    "summary": {"value": "有2年后端开发经验", "confidence": 0.85},
}


def run_mock_interview():
    print("=" * 70)
    print("模拟面试循环（逐题交互）")
    print("=" * 70)
    config = {"configurable": {"thread_id": "mock-1"}}
    result = mock_interview_engine.invoke(
        {"request_type": "mock_interview", "fields": FIELDS, "level": "中级"},
        config,
    )

    for turn in range(20):
        q = result.get("current_question") or {}
        if not q:
            print("[无题目] 提前结束")
            break
        tag = "追问" if q.get("type") == "follow_up" else "主问题"
        print(f"第 {turn + 1} 轮({tag}/{q.get('category')}): {q.get('question')}")

        # 模拟用户作答
        answer = f"这是第{turn + 1}轮的参考答案，我进行了相关的实践。"
        mock_interview_engine.update_state(config, {"user_answer": answer})
        result = mock_interview_engine.invoke(None, config)

        feedback = result.get("feedback")
        if feedback:
            print(f"  得分: {feedback.get('score')} | 追问: {feedback.get('follow_up')}")

        if result.get("report") is not None:
            report = result["report"]
            print("-" * 70)
            print("面试评估报告:")
            print("  总分:", report.get("total_score"))
            print("  维度:", report.get("dimensions"))
            print("  亮点:", report.get("highlights"))
            print("  建议:", report.get("suggestions"))
            print("  问答记录数:", len(report.get("qa_records", [])))
            break


def run_entry_router():
    print()
    print("=" * 70)
    print("入口路由：coaching")
    print("=" * 70)
    result = qa_engine.invoke(
        {"request_type": "coaching", "question": "介绍你最有挑战的项目", "fields": FIELDS},
        {"configurable": {"thread_id": "router-1"}},
    )
    print("intent:", result.get("intent"))
    print("answer 前 60 字:", (result.get("answer") or "")[:60])
    print("citations:", result.get("citations"))
    print("session_id:", result.get("session_id"))


if __name__ == "__main__":
    run_mock_interview()
    run_entry_router()
