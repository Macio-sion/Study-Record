"""
多格式文本提取工具（节点二：多格式解析）

策略：按文件真实格式（file_type）分派到对应解析器，统一遵循
「文本层优先 → 图片 OCR → 大模型 OCR 兜底」的降级链路。

文本与版式信息并行输出（方案 B）：
- text        纯文本，供结构化信息提取（节点四）使用
- page_count  页数（从字节流解析，无需外部元数据）
- layout      版式信息（按页组织，含页面尺寸 + 文本块/图片块 + 坐标），供复杂排版还原（节点三）使用
- ocr_used    是否走了 OCR（扫描件/图片标记，供下游置信度评估）
- source_type 真实文件格式

统一输出结构：
{
    "text": str,
    "page_count": int,
    "layout": {
        "pages": [
            {
                "page": int,
                "width": float | None,
                "height": float | None,
                "blocks": [
                    {"type": "text",  "bbox": [x0,y0,x1,y1] | None, "text": str},
                    {"type": "image", "bbox": [x0,y0,x1,y1] | None, "ext": str, "image_index": int},
                ]
            }
        ]
    },
    "ocr_used": bool,
    "source_type": str,
}

注：图片块只保留元信息（bbox/ext/image_index），图片二进制可用 fitz 按需提取，
避免将大体积二进制塞入状态导致膨胀。
"""

import io
from pypdf import PdfReader


# ---------------------------------------------------------------------------
# 文本质量判定（硬编码规则）
# ---------------------------------------------------------------------------

def _is_garbled_char(ch: str) -> bool:
    """判断字符是否为乱码"""
    code = ord(ch)
    if code == 0xFFFD:
        return True
    if code < 0x20 and ch not in ["\n", "\r", "\t"]:
        return True
    if code >= 0xE000 and code <= 0xFFFF:
        return True
    if code >= 0xD800 and code <= 0xDFFF:
        return True
    return False


def _garbled_ratio(text: str) -> float:
    """计算乱码字符比例"""
    total = 0
    garbled = 0
    for ch in text:
        if ch.isspace():
            continue
        total += 1
        if _is_garbled_char(ch):
            garbled += 1
    return garbled / total if total > 0 else 0


def _test_scan(text: str) -> bool:
    """测试读取文本的质与量，返回 True 表示判为扫描件"""
    if not text.strip():
        return True
    if _garbled_ratio(text) > 0.5:
        return True
    return False


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _extract_pdf_text(data: bytes) -> str:
    """提取 PDF 文本层"""
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_pdf_page_count(data: bytes) -> int:
    """用 pypdf 获取 PDF 页数（从字节流解析，无需外部元数据）"""
    try:
        return len(PdfReader(io.BytesIO(data)).pages)
    except Exception:
        return 0


def _extract_page_lines(page) -> list:
    """提取页面的横线/竖线（表格线/分割线），返回 line 块列表"""
    lines = []
    try:
        drawings = page.get_drawings()
    except Exception:
        return lines
    for d in drawings:
        for item in d.get("items", []):
            if item[0] != "l":  # 只处理线段
                continue
            p1, p2 = item[1], item[2]
            x0, y0, x1, y1 = p1.x, p1.y, p2.x, p2.y
            if abs(y1 - y0) < 0.5 and abs(x1 - x0) > 20:  # 横线（长度>20pt，过滤下划线）
                lines.append({"type": "line", "bbox": [min(x0, x1), y0, max(x0, x1), y1],
                              "orientation": "horizontal"})
            elif abs(x1 - x0) < 0.5 and abs(y1 - y0) > 20:  # 竖线
                lines.append({"type": "line", "bbox": [x0, min(y0, y1), x1, max(y0, y1)],
                              "orientation": "vertical"})
    return lines


def _extract_pdf_layout(data: bytes) -> dict:
    """提取 PDF 版式信息（按页组织，含页面尺寸 + 文本块/图片块/线条 + 坐标），依赖 pymupdf"""
    try:
        import pymupdf
    except ImportError:
        return {"pages": []}

    doc = pymupdf.open(stream=data, filetype="pdf")
    pages = []
    image_index = 0
    for page_no in range(len(doc)):
        page = doc[page_no]
        page_dict = page.get_text("dict")
        page_blocks = []
        for block in page_dict.get("blocks", []):
            bbox = list(block.get("bbox", ()))
            if block.get("type") == 0:  # 文本块
                line_texts = [
                    "".join(span.get("text", "") for span in line.get("spans", []))
                    for line in block.get("lines", [])
                ]
                page_blocks.append({
                    "type": "text",
                    "bbox": bbox,
                    "text": "\n".join(line_texts),
                })
            elif block.get("type") == 1:  # 图片块
                page_blocks.append({
                    "type": "image",
                    "bbox": bbox,
                    "ext": block.get("ext", ""),
                    "image_index": image_index,
                })
                image_index += 1
        # 提取线条（表格线/分割线）
        page_blocks.extend(_extract_page_lines(page))
        pages.append({
            "page": page_no,
            "width": page_dict.get("width", 0),
            "height": page_dict.get("height", 0),
            "blocks": page_blocks,
        })
    return {"pages": pages}


def extract_pdf_images(data: bytes) -> list:
    """按需提取 PDF 中所有图片的二进制（供下游保存头像/作品图等）"""
    try:
        import pymupdf
    except ImportError:
        return []

    doc = pymupdf.open(stream=data, filetype="pdf")
    images = []
    for page_no in range(len(doc)):
        for xref, *_ in doc[page_no].get_images(full=True):
            info = doc.extract_image(xref)
            images.append({
                "page": page_no,
                "xref": xref,
                "ext": info.get("ext", ""),
                "image": info.get("image", b""),
            })
    return images


def _pdf_to_images(data: bytes) -> list:
    """将 PDF 每页转为图片字节流（依赖 pymupdf/fitz）"""
    try:
        import pymupdf
    except ImportError:
        return []
    doc = pymupdf.open(stream=data, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        images.append(pix.tobytes("png"))
    return images


def extract_pdf(data: bytes) -> dict:
    """PDF 解析：文本层 + 版式信息并行输出，文本为空（扫描件）降级 OCR"""
    text = _extract_pdf_text(data)
    page_count = _extract_pdf_page_count(data)
    layout = _extract_pdf_layout(data)

    if not _test_scan(text):
        return {
            "text": text,
            "page_count": page_count,
            "layout": layout,
            "ocr_used": False,
            "source_type": "pdf",
        }

    images = _pdf_to_images(data)
    if images:
        ocr_text = "\n".join(ocr_image(img) for img in images)
        if ocr_text.strip():
            return {
                "text": ocr_text,
                "page_count": page_count,
                "layout": layout,
                "ocr_used": True,
                "source_type": "pdf",
            }

    # 文本层与 OCR 均失败
    return {
        "text": "",
        "page_count": page_count,
        "layout": layout,
        "ocr_used": False,
        "source_type": "pdf",
    }


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------

def extract_docx(data: bytes) -> dict:
    """DOCX 解析：直接读 OOXML 段落与表格（本质是 XML，有文本层）"""
    try:
        from docx import Document
    except ImportError:
        return {"text": "", "page_count": 0, "layout": {"pages": []},
                "ocr_used": False, "source_type": "docx"}

    doc = Document(io.BytesIO(data))
    blocks = []
    text_parts = []

    # 注：docx 无像素坐标，bbox 置 None；paragraphs/tables 分开遍历，交叉顺序暂不还原
    for p in doc.paragraphs:
        if p.text and p.text.strip():
            blocks.append({"type": "paragraph", "bbox": None, "text": p.text})
            text_parts.append(p.text)

    for table in doc.tables:
        row_texts = [" | ".join(cell.text for cell in row.cells) for row in table.rows]
        table_text = "\n".join(row_texts)
        blocks.append({"type": "table", "bbox": None, "text": table_text})
        text_parts.append(table_text)

    return {
        "text": "\n".join(text_parts),
        "page_count": 1,  # docx 不分页，page_count 无实际意义，占位为 1
        "layout": {"pages": [
            {"page": 0, "width": None, "height": None, "blocks": blocks}
        ]},
        "ocr_used": False,
        "source_type": "docx",
    }


def extract_doc(data: bytes) -> dict:
    """
    DOC（老式二进制 OLE）解析：
    优先 LibreOffice 转 docx 后复用 extract_docx，转换失败转图片 OCR 兜底。
    """
    # TODO: soffice --headless --convert-to docx 转换后复用 extract_docx
    # TODO: 转换失败时转图片，走 ocr_image
    return {"text": "", "page_count": 0, "layout": {"pages": []},
            "ocr_used": False, "source_type": "doc"}


# ---------------------------------------------------------------------------
# 图片 / OCR
# ---------------------------------------------------------------------------

def _tesseract_ocr(img_bytes: bytes) -> str:
    """第一级：本地 tesseract OCR"""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""
    try:
        return pytesseract.image_to_string(
            Image.open(io.BytesIO(img_bytes)), lang="chi_sim+eng"
        )
    except Exception:
        return ""


def _llm_ocr(img_bytes: bytes) -> str:
    """第二级：大模型多模态 OCR 兜底"""
    # TODO: 复用 llm/client.py 的多模态能力，将图片作为视觉输入传给模型
    return ""


def ocr_image(img_bytes: bytes) -> str:
    """OCR 两级降级：tesseract → 大模型兜底"""
    text = _tesseract_ocr(img_bytes)
    if text.strip():
        return text
    return _llm_ocr(img_bytes)


def extract_image(data: bytes, file_type: str) -> dict:
    """图片解析：无文本层，直接 OCR"""
    return {
        "text": ocr_image(data),
        "page_count": 1,
        "layout": {"pages": [
            {"page": 0, "width": None, "height": None, "blocks": [
                {"type": "image", "bbox": None, "ext": file_type, "image_index": 0}
            ]}
        ]},
        "ocr_used": True,
        "source_type": file_type,
    }


# ---------------------------------------------------------------------------
# 统一分派入口
# ---------------------------------------------------------------------------

_HANDLERS = {
    "pdf": extract_pdf,
    "docx": extract_docx,
    "doc": extract_doc,
    "png": lambda d: extract_image(d, "png"),
    "jpg": lambda d: extract_image(d, "jpg"),
}


def extract_text(data: bytes, file_type: str) -> dict:
    """多格式文本提取统一入口，按 file_type 分派到对应解析器"""
    handler = _HANDLERS.get(file_type)
    if handler is None:
        return {"text": "", "page_count": 0, "layout": {"pages": []},
                "ocr_used": False, "source_type": file_type or "unknown"}
    return handler(data)


if __name__ == "__main__":
    with open(r"D:\0_VG\source\04_综合项目\07_简历智能体\test\datas\260419973596063.pdf", "rb") as f:
        data = f.read()
        result = extract_pdf(data)
        print("page_count:", result["page_count"])
        print("ocr_used:", result["ocr_used"])
        print("layout pages:", len(result["layout"]["pages"]))
        print("text preview:", result["text"][:500])
