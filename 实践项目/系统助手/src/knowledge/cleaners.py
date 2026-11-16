"""知识文档数据清洗。

移除空文档，并按正文内容哈希去重。
"""

from __future__ import annotations

import hashlib
from typing import List

from langchain_core.documents import Document


def clean_documents(documents: List[Document]) -> List[Document]:
    """清洗文档：去除空白正文文档，并按内容哈希去重。

    Args:
        documents: 原始文档列表。

    Returns:
        清洗后的文档列表（保持原始顺序）。
    """
    cleaned: List[Document] = []
    seen: set = set()
    for doc in documents:
        content = (doc.page_content or "").strip()
        if not content:
            continue
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        doc.page_content = content
        cleaned.append(doc)
    return cleaned


__all__ = ["clean_documents"]
