from state.resume_state import ResumeState
from services.document_processing_engine.file_vaild_tools import validate_format, validate_encrypted, validate_integrity
from services.document_processing_engine.file_parse_tools import extract_text
from services.document_processing_engine.layout_process import is_body, concat_text, order_page_blocks
from services.document_processing_engine.structure_extract import extract_structured, calibrate
from services.document_processing_engine.validate_result import validate


def validate_file(state: ResumeState) -> dict:
    """
    文件校验节点：格式 → 加密 → 损坏，任一失败即中断流水线
    """
    file_source = state.get("file_source")
    if not file_source:
        return {"error_data": {
            "code": "PARSE_EMPTY",
            "module": "validate_file",
            "message": "文件为空，请重新上传",
            "place": "file_source",
        }}

    # 校验文件格式
    format_result = validate_format(file_source)
    if not format_result["ok"]:
        return {"error_data": {
            "code": "PARSE_FORMAT_ERROR",
            "module": "validate_format",
            "message": format_result["message"],
            "place": "file_source",
        }}

    extension = format_result["extension"]

    # 校验文件加密
    if not validate_encrypted(file_source, extension):
        return {"error_data": {
            "code": "PARSE_ENCRYPTED",
            "module": "validate_encrypted",
            "message": "文件已加密，请解除加密后上传",
            "place": "file_source",
        }}

    # 校验文件完整性
    if not validate_integrity(file_source, extension):
        return {"error_data": {
            "code": "PARSE_CORRUPTED",
            "module": "validate_integrity",
            "message": "文件已损坏，请重新导出后上传",
            "place": "file_source",
        }}

    return {
        "file_valid": True,
        "file_type": extension,
    }


def parse_file(state: ResumeState) -> dict:
    """
    解析文件内容，提取简历信息（节点二：多格式解析）
    """
    file = state.get("file_source")
    if not file:
        return {"error_data": {
            "code": "PARSE_EMPTY",
            "module": "parse_file",
            "message": "文件为空，请重新上传",
            "place": "file_source",
        }}
    if not state.get("file_valid", False):
        return {"error_data": {
            "code": "PARSE_NOT_VALIDATED",
            "module": "parse_file",
            "message": "文件未验证",
            "place": "file_valid",
        }}
    file_type = state.get("file_type")
    result = extract_text(file, file_type)
    if not result['text']:
        return {
            "error_data": {
                "code": "PARSE_FAILED",
                "module": "parse_file",
                "message": "文件解析失败，请检查文件格式",
                "place": "text",
            }
        }
    return {
        "text": result["text"],
        "page_count": result["page_count"],
        "layout": result["layout"],
        "ocr_used": result["ocr_used"],
        "source_type": file_type,
    }


def layout_process(state: ResumeState) -> dict:
    """
    节点三：复杂排版还原（分栏 + 表格行聚类 + 阅读顺序重排）
    """
    layout = state.get("layout", {})
    pages = layout.get("pages", [])
    if not pages:
        return {}

    ordered_blocks = []
    is_single_page = len(pages) == 1
    for page_info in pages:
        page_no = page_info.get("page", 0)
        height = page_info.get("height") or 0
        width = page_info.get("width") or 0
        blocks = page_info.get("blocks", [])

        # 剥离页眉页脚（单页文档无跨页重复页眉，跳过剥离）
        if is_single_page:
            body = blocks
        else:
            body = [b for b in blocks if is_body(b, height)]

        # 分栏 + 表格行聚类 + 阅读顺序重排
        page_ordered = order_page_blocks(body, width)

        for b in page_ordered:
            block = dict(b)
            block["page"] = page_no
            ordered_blocks.append(block)

    return {
        "ordered_blocks": ordered_blocks,
        "reading_text": concat_text(ordered_blocks),
        "layout_processed": True,
    }


def structure_extract(state: ResumeState) -> dict:
    """
    节点四：结构化信息提取（LLM 提取语义字段 + 正则直提确定性字段）
    """
    text = state.get("reading_text") or state.get("text")
    if not text:
        return {"error_data": {
            "code": "PARSE_NO_TEXT",
            "module": "structure_extract",
            "message": "无文本可提取，请检查前置节点",
            "place": "reading_text",
        }}

    result = extract_structured(text)
    fields, pending = calibrate(result, text)

    return {
        "fields": fields,
        "pending": pending,
    }


def validate_result(state: ResumeState) -> dict:
    """
    节点五：解析结果校验与补全（必填缺失 + 置信度阈值 + 格式合法性）
    """
    fields = state.get("fields")
    if not fields:
        return {"error_data": {
            "code": "PARSE_NO_FIELDS",
            "module": "validate_result",
            "message": "无结构化字段可校验，请检查前置节点",
            "place": "fields",
        }}

    report, pending = validate(fields)
    return {
        "validation_report": report,
        "pending": pending,
    }

def should_continue(state: ResumeState) -> str:
    """交接模式：检查节点是否出错，有错则中断流水线"""
    if state.get("error_data"):
        return "end"
    return "continue"