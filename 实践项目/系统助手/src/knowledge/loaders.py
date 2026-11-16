"""知识文档加载器。

从知识库目录 ``/knowledge/{type}/`` 加载 PDF 文档，返回带类型元数据的
LangChain ``Document`` 列表。当前仅支持 PDF，后续可扩展其他类型。
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def list_knowledge_types(knowledge_dir: Path) -> List[str]:
    """列出知识库目录下的所有文档类型（子目录名）。"""
    if not knowledge_dir.exists():
        return []
    return sorted(p.name for p in knowledge_dir.iterdir() if p.is_dir())


def load_pdf_documents(knowledge_dir: Path, doc_type: str) -> List[Document]:
    """加载指定类型目录下的全部 PDF 文档。

    Args:
        knowledge_dir: 知识库根目录（绝对路径）。
        doc_type: 文档类型（子目录名）。

    Returns:
        带 ``type`` 与 ``source`` 元数据的 Document 列表。
    """
    type_dir = knowledge_dir / doc_type
    if not type_dir.is_dir():
        return []

    documents: List[Document] = []
    for pdf_path in sorted(type_dir.iterdir()):
        if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
            continue
        loader = PyPDFLoader(str(pdf_path))
        for doc in loader.load():
            doc.metadata.setdefault("type", doc_type)
            doc.metadata.setdefault("source", str(pdf_path))
            documents.append(doc)
    return documents


__all__ = ["list_knowledge_types", "load_pdf_documents"]
