"""文本切分单元测试。"""

from __future__ import annotations

from langchain_core.documents import Document

from knowledge.splitter import split_documents


def test_split_long_document():
    """长文档被切分为多个块。"""
    text = "这是一个测试段落。" * 500
    chunks = split_documents(
        [Document(page_content=text)],
        chunk_size=1024,
        chunk_overlap=256,
        min_chunk_size=0,
    )
    assert len(chunks) > 1
    assert all(len(c.page_content) <= 1024 for c in chunks)


def test_start_index_present():
    """切分后的块包含 start_index 元数据。"""
    chunks = split_documents(
        [Document(page_content="x" * 3000)],
        chunk_size=1024,
        chunk_overlap=256,
        min_chunk_size=0,
    )
    assert chunks
    assert "start_index" in chunks[0].metadata


def test_min_chunk_size_filter():
    """过小的块被过滤。"""
    chunks = split_documents(
        [Document(page_content="short")],
        chunk_size=1024,
        chunk_overlap=256,
        min_chunk_size=100,
    )
    assert chunks == []


def test_no_chunks_for_short_document():
    """短文档在默认 min_chunk_size 下无有效块。"""
    chunks = split_documents([Document(page_content="hi")], min_chunk_size=256)
    assert chunks == []


def test_min_chunk_size_disabled():
    """min_chunk_size=0 时不过滤。"""
    chunks = split_documents(
        [Document(page_content="hi")],
        chunk_size=1024,
        chunk_overlap=256,
        min_chunk_size=0,
    )
    assert len(chunks) == 1
