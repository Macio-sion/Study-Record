from typing import TypedDict, Optional

from utils.error import ErrorMessage


class ResumeState(TypedDict, total=False):
    """简历解析工作流状态（节点间交接的数据契约）"""

    # 输入
    file_source: bytes                   # 网络传输的原始字节流（核心输入，实际必填）
    file_name: str                       # 源文件名

    # 文件校验
    file_valid: Optional[bool]           # 文件校验结果
    file_type: Optional[str]             # 识别出的真实文件格式（pdf/docx/doc/png/jpg）
    # 文件解析
    text: Optional[str]                  # 提取到的纯文本/半结构化文本
    page_count: Optional[int]            # 页数
    layout: Optional[dict]               # 版式信息（文本块/图片块 + 坐标 + 页号）
    ocr_used: Optional[bool]             # 是否走了 OCR（扫描件/图片标记，供下游置信度评估）
    source_type: Optional[str]           # 真实文件格式（pdf/docx/doc/png/jpg）
    
    # 布局处理（节点三）
    layout_processed: Optional[bool]     # 是否处理过布局
    ordered_blocks: Optional[list]       # 按阅读顺序重排后的内容块
    reading_text: Optional[str]          # 按阅读顺序拼接的纯文本

    # 结构化提取（节点四）
    fields: Optional[dict]               # 结构化字段（value + confidence）
    pending: Optional[list]              # 待确认/待补充字段清单

    # 结果校验（节点五）
    validation_report: Optional[dict]    # 校验报告（缺失/低置信度/格式非法）

    # 错误处理结果
    error_data: Optional[ErrorMessage]   # 统一错误信息
