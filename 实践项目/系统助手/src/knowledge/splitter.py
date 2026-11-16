"""文本切分器。

使用 ``RecursiveCharacterTextSplitter`` 对文档进行递归字符切分，并为每个块
添加起始索引（``start_index``）便于后续查询定位。
"""

from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    documents: List[Document],
    chunk_size: int = 1024,
    chunk_overlap: int = 256,
    min_chunk_size: int = 256,
) -> List[Document]:
    """切分文档，并过滤掉过小的块。

    Args:
        documents: 待切分文档。
        chunk_size: 每个块的目标最大长度。
        chunk_overlap: 相邻块重叠长度。
        min_chunk_size: 最小块长度，小于该值的块被丢弃。

    Returns:
        切分后的 Document 列表（含 ``start_index`` 元数据）。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    if min_chunk_size <= 0:
        return chunks
    return [chunk for chunk in chunks if len(chunk.page_content) >= min_chunk_size]


__all__ = ["split_documents"]
