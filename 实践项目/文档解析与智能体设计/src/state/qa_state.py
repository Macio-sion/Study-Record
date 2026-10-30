from typing import TypedDict, Optional

from utils.error import ErrorMessage


class QaState(TypedDict, total=False):
    """简历智能问答工作流状态（节点间交接的数据契约）

    复用解析引擎产出的 StructuredResume.fields 作为唯一简历数据源，
    覆盖「模拟面试」与「面试辅导」两个子图的输入与中间态。
    """

    # 入口路由
    request_type: str                       # mock_interview / coaching

    # 简历数据（复用解析引擎 StructuredResume）
    resume_id: str                          # 简历 ID
    fields: dict                            # StructuredResume.fields（value + confidence）

    # 模拟面试输入
    jd: Optional[str]                       # 目标岗位 JD（可选）
    level: Optional[str]                    # 岗位级别：初级/中级/高级/专家

    # 面试辅导输入
    question: Optional[str]                 # 用户提问 / 面试题
    session_id: Optional[str]               # 会话 ID（多轮，首轮省略）

    # 模拟面试中间态
    context_ready: Optional[bool]           # 上下文是否就绪
    difficulty_profile: Optional[dict]      # { tag, depth, ratio }
    question_list: Optional[dict]           # { technical, behavioral, case }
    current_question: Optional[dict]        # { id, question }
    progress: Optional[dict]                # { asked, total }
    interview_status: Optional[str]         # asking / answering / done
    user_answer: Optional[str]              # 用户作答（evaluate 输入）
    feedback: Optional[dict]                # { score, comment, follow_up }
    pending_follow_up: Optional[str]        # 待追问的问题（evaluate 生成，ask 抛出）
    qa_records: Optional[list]              # 问答记录（question/answer/score，供总结报告）
    report: Optional[dict]                  # InterviewReport

    # 面试辅导中间态
    intent: Optional[str]                   # 技术面/行为面/案例面/通用
    intent_confidence: Optional[float]      # 意图置信度
    retrieved: Optional[list]               # [{ source, field, text, score }]
    answer: Optional[str]                   # 生成的参考答案
    citations: Optional[list]               # 引用的简历字段定位
    history: Optional[list]                 # 多轮对话历史

    # 错误处理
    error_data: Optional[ErrorMessage]      # 统一错误信息
