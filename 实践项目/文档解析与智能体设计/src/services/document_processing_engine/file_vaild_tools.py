import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

# 支持格式的文件签名（魔数）
SIGNATURES = {
    b"%PDF-": "pdf",
    b"\x50\x4b\x03\x04": "docx",
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "doc",
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
}


def detect_format(file_obj: bytes) -> str:
    """
    基于魔数识别文件真实格式（不依赖扩展名/content-type）
    """
    head = file_obj[:16]
    for sig, ext in SIGNATURES.items():
        if head.startswith(sig):
            return ext
    return "unknown"


def validate_format(file_obj: bytes) -> dict:
    """
    文件格式校验
    """
    ext = detect_format(file_obj)
    if ext == "unknown":
        return {"ok": False, "extension": ext, "message": "文件格式未知"}
    return {"ok": True, "extension": ext, "message": f"文件格式正确: {ext}"}


def validate_encrypted(file_obj: bytes, extension: str) -> bool:
    """
    文件加密校验，返回 True 表示未加密
    """
    if extension != "pdf":
        # docx/doc/png/jpg 的加密检测逻辑 TODO：按需实现
        return True
    try:
        reader = PdfReader(io.BytesIO(file_obj))
        return not reader.is_encrypted
    except Exception:
        return False


def validate_integrity(file_obj: bytes, extension: str) -> bool:
    """
    文件完整性校验，返回 True 表示文件完整可读
    """
    if not file_obj:
        return False
    try:
        if extension == "pdf":
            reader = PdfReader(io.BytesIO(file_obj))
            _ = len(reader.pages)
            for page in reader.pages:
                page.extract_text()
            return True
        # docx/doc/png/jpg 的完整性校验逻辑 TODO：按需实现
        return True
    except PdfReadError:
        return False
    except Exception:
        return False


if __name__ == "__main__":
    with open("test.pdf", "rb") as f:
        result = validate_format(f.read())
        print(result)
