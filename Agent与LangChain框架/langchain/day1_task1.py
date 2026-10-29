from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig, ConfigurableField, RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain.messages import AIMessage, HumanMessage
from langgraph.graph import add_messages
from langchain.tools import tool

model_name = "qwen2.5:7b-instruct-q4_K_M"

def log_input(inputs: dict) -> dict:
    """
    输出到终端
    """
    print(f"Logging input: {inputs}")
    return inputs

def truncate_output(text: str, max_length: int = 100) -> str:
    """截断过长的输出"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

# 1. 定义提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("human", "{question}") # 通过模板内的format方法将question变量替换为实际的输入
])

# 2. 定义模型
model = ChatOllama(model="qwen3.5:0.8b").configurable_fields(
    model=ConfigurableField(
        id="model",
        description="The name of the model to use.",  
    ),
    temperature=ConfigurableField(
        id="temperature",
        description="The temperature to use for sampling.",
    )
)

# 3. 定义解析器
parser = StrOutputParser()

# for chunk in chain.stream({"question": "什么是LCEL？"}):
#     print(chunk, end="", flush=True)

# 4. 构建链
chain = RunnableLambda(log_input) | prompt | model | parser
# chain =  model | parser

result = chain.invoke(
    {
        "question": "讲个笑话。"
    },
    config=RunnableConfig(
        model=model_name,
        temperature=0.8
    )
)

# result = chain.invoke(
#     input={
#         "messages": [HumanMessage(content="讲个笑话。")],
#     },
#     config=RunnableConfig(
#         model=model_name,
#         temperature=0.8
#     )
# )

print(type(result), result)

# # 5. 测试调用
# result = chain.invoke({"question": "什么是LCEL？"})
# print(result)

# # 6. 流式调用
# for chunk in chain.stream({"question": "什么是LCEL？"}):
#     print(chunk, end="", flush=True)