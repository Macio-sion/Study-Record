from langchain_community.document_loaders import (
    PyPDFDirectoryLoader,
    DirectoryLoader,
    PyPDFLoader,  # 负责PDF的读取与解码
    TextLoader,
    WebBaseLoader,
    CSVLoader
) # 本质加载, 难在对目标数据的处理效果，通常需要打补
from collections import defaultdict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import (
    PGEngine,          # 负责链接，执行底层的SQL语句（表的创建）
    PGVectorStore,     # 向量数据库的检索
    Column             # 向量表的字段
)
from langchain_core.documents import Document
from langchain.embeddings import Embeddings, init_embeddings
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.tools import tool


# ======================================
# ============== knowledge build ==============
# ======================================
loader = PyPDFDirectoryLoader(r"D:\0_VG\data\knowledge_base")
docs = loader.load()
print(type(docs[0]), "\n", docs[0])

documents_by_file = defaultdict(list)
for doc in docs:
    documents_by_file[doc.metadata["source"]].append(doc)









# ======================================
# ============== knowledge retrieval =========
# ======================================

if __name__ == "__main__":
    pass