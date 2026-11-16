import inspect
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector as PGVector2

print("PGVector sig:")
print(inspect.signature(PGVector.__init__))
