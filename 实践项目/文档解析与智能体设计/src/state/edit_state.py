from typing import TypedDict, Optional

from utils.error import ErrorMessage


class EditState(TypedDict, total=False):
    """简历智能生成与优化工作流状态（节点间交接的数据契约）

    复用解析引擎产出的 StructuredResume.fields 作为唯一简历数据源，
    覆盖「简历生成」「逐条优化」「一键应用」「版本对比」四个子流程。
    """

    # 入口路由
    request_type: str                       # generate / optimize / apply / diff

    # 简历数据（复用解析引擎 StructuredResume）
    resume_id: str                          # 简历 ID
    fields: dict                            # StructuredResume.fields（value + confidence）
    manual_input: dict                      # 手动输入（简历生成来源，可选）

    # 生成/优化输入
    jd: Optional[str]                       # 目标岗位 JD（可选）
    optimize_types: Optional[list]          # 需执行的优化类型，缺省执行全部

    # 信息获取（节点一）
    resume_data: Optional[dict]             # 统一简历数据结构（fields）
    context_ready: Optional[bool]           # 上下文是否就绪

    # 简历生成 / 逐条优化（节点二）
    generated_resume: Optional[dict]        # 简历生成产出的整份简历 fields
    suggestions: Optional[list]             # EditSuggestion[]（优化建议）

    # 一键应用与对比（节点三）
    suggestion_ids: Optional[list]          # 逐条应用时指定 ID 列表
    accept_all: Optional[bool]              # true 全部接受
    version: Optional[str]                  # 版本号（应用后新版本 / 对比目标版本）
    base_version: Optional[str]             # 对比基准版本（缺省上一版本）
    updated_fields: Optional[list]          # 应用后更新的字段定位列表
    diffs: Optional[list]                   # 版本对比结果

    # 错误处理
    error_data: Optional[ErrorMessage]      # 统一错误信息
