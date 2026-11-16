"""知识文档清洗单元测试。"""

from __future__ import annotations

from langchain_core.documents import Document

from knowledge.cleaners import clean_documents


def test_remove_blank_documents():
    """空白文档被移除。"""
    docs = [
        Document(page_content="   ", metadata={}),
        Document(page_content="\n\t", metadata={}),
        Document(page_content="有效内容", metadata={}),
    ]
    result = clean_documents(docs)
    assert [d.page_content for d in result] == ["有效内容"]


def test_deduplicate_by_content():
    """相同正文去重，保留首次出现。"""
    docs = [
        Document(page_content="hello", metadata={"src": "a"}),
        Document(page_content="hello", metadata={"src": "b"}),
        Document(page_content="world", metadata={"src": "c"}),
    ]
    result = clean_documents(docs)
    assert [d.page_content for d in result] == ["hello", "world"]
    assert result[0].metadata["src"] == "a"


def test_strip_whitespace():
    """正文首尾空白被去除。"""
    docs = [Document(page_content="  hello world  ")]
    assert clean_documents(docs)[0].page_content == "hello world"


def test_empty_input():
    """空列表返回空列表。"""
    assert clean_documents([]) == []
