# from __future__ import annotations
# from langgraph.graph import StateGraph, END
# from langgraph.types import Send  # Send的两种用法
# from typing import Literal, Annotated, TypedDict
# from langchain.messages import HumanMessage, SystemMessage
# from pydantic import BaseModel, Field
# from langchain_ollama import ChatOllama
# from IPython.display import Image, display
# import operator

# model_name = "qwen2.5:7b-instruct-q4_K_M"
# model = ChatOllama(model=model_name)

# class Section(BaseModel):
#     name: str = Field(description="这一节的标题或名称。")
#     contents: str = Field(description="这一节的概要内容。")

# class Chapter(BaseModel):
#     name: str = Field(description="这一章的标题或名称。")
#     contents: str = Field(description="这一章的概要内容。")
#     sections: list[Section] = Field(description="本章下的所有节内容，类型为section列表。")

# class Book(BaseModel):
#     chapters: list[Chapter] = Field(description="本书下的所有章内容，章下包含节的细节。")

# planner = model.with_structured_output(Book)

# class Creative_writing_State(TypedDict):
#     # 输入数据
#     book_name: str
#     topic: str
#     # 中间状态数据
#     # 传递
#     chapters: list[Chapter] | None  #  章名列表
#     # 中间状态数据
#     # 接收
#     completed_chapters: Annotated[list, operator.add]   # 章的中间处理list
#     completed_sections: Annotated[list, operator.add] # 节的中间处理list
#     # 输出数据
#     final_outputs: str

# class Chapter_gene_State(TypedDict):
#     # 输入数据
#     chapter: Chapter  # 章信息

#     chapter_result: str  # 完成的章内容
#     sections_result: Annotated[list, operator.add]  
    

# class Section_gene_State(TypedDict):
#     # 输入数据
#     chapter_name: str  # 章名
#     section: Section  # 节名
#     # 中间状态数据
#     section_result: str  # 完成的节内容
#     # 判断
#     evals: Literal["pass", "refuse"]
#     # 建议
#     rewrite_advice: str

# class Evalution(BaseModel):
#     evals: Literal["pass", "refuse"] = Field(description="评判本节内容是否与节主题符合。符合为pass，不符合为refuse。")
#     rewrite_advice: str = Field(description="若评判为不符合，生成改进建议，让其在次生成的内容符合要求。")

# evaluator = model.with_structured_output(Evalution)

# # 节点
# def orchestrator(state: Creative_writing_State) -> dict:
#     """
#     编排器，生成总体任务的大纲
#     """
#     system_prompt = f"""
#     根据用户提出的主题，生成结构化的报告内容。
#     要求逻辑严谨，章与章之间相互关联，有前后关系。章下的多个节之间相互联系。每个章下节的数量不得少于2节，不得大于5节。章的数量无限制。
#     """
#     report_gene_prompt = f"""
#     根据以下的主题：{state['topic']}与书的名称: {state['book_name']}，创作其下的章节。内容开放。
#     """
#     result = planner.invoke([SystemMessage(content=system_prompt),HumanMessage(content=report_gene_prompt)])
#     return {
#         "chapters": result.chapters
#     }

# def llm_call_gene_chapter(state: Chapter_gene_State) -> dict:
#     """
#     章概要生成器，批量生成章内容的工作节点
#     """
#     system_prompt = f"""
#     根据已有的章名与内容，补充与完善章概要的设计。
#     """
#     report_gene_prompt = f"""
#     当前章名是：{state['chapter'].name},章概要是: {state['chapter'].contents}，对目前的章概要进行完善与补充。
#     """
#     result = model.invoke([SystemMessage(content=system_prompt),HumanMessage(content=report_gene_prompt)])
#     return {
#         "chapter_result": result.content,
#         "chapter": state['chapter']
#     }

# def llm_call_gene_section(state: Section_gene_State) -> dict:
#     """
#     节内容生成器，批量生成节内容的工作节点
#     """
#     system_prompt = f"""
#     根据已有的节信息，设计本节内容的核心。
#     """
#     report_gene_prompt = f"""
#     当前章名是：{state['chapter_name']}，对应的节名是：{state['section'].name},节概要是: {state['section'].contents}，请设计本节的核心内容。
#     """
#     if state.get("evals", "") == "refuse":
#         system_prompt += f"根据主编的建议，改进并重写节的内容。改进建议是:{state['rewrite_advice']}。"
#         result = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])
#     else:
#         result = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])
#     return {
#         "sections_result": [{
#             "chapter_name": state['chapter_name'],
#             "section_name": state['section'].name,
#             "content": result.content
#         }]
#     }

# def evaluator_for_section(state: Section_gene_State) -> dict:
#     """
#     优化评判节点
#     """
#     system_prompt = f"""
#     你是一位资深的主编，专门为章节评判进行分辨。
#     任务是对用户提出的设计进行分析与判断，给出evals和修改建议，如果evals通过为pass则无需提供建议。
#     按格式化输出。
#     """
#     report_gene_prompt = f"""
#     目前节的内容名称是:{state['section'].name}, 内容是:{state['section_result']}。请进行评判。
#     """
#     grade = evaluator.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])

#     return {
#         "evals": grade.evals,
#         "rewrite_advice": grade.rewrite_advice
#     }

# def send_task_chapter(state: Creative_writing_State) -> list[Send]:
#     """
#     任务分发，将章任务分发
#     """
#     return [Send("llm_call_gene_chapter", {"chapter": c}) for c in state["chapters"]]

# def chapter_combine(state: Chapter_gene_State) -> dict:
#     """
#     章内容汇聚，将章内容汇聚到主state中
#     """
#     return {
#         "completed_chapters": [state["chapter_result"]],
#         "completed_sections": state.get("sections_result", [])
#     }

# def send_task_section(state: Chapter_gene_State) -> list[Send]:
#     """
#     任务分发，将章下的各节任务分发
#     """
#     sends = []
#     for s in state["chapter"].sections:
#         sends.append(
#             Send(
#                 "sub_graph",
#                 {
#                     "chapter_name": state["chapter"].name, 
#                     "section": s
#                 }   
#             )
#         )
#     return sends
        
# def router_section(state: Section_gene_State) -> str:
#     """
#     优化内容的路由
#     """
#     if state['evals'] == "pass":
#         return "pass"
#     if state['evals'] == "refuse":
#         return "refuse"
    
# def conbine(state: Creative_writing_State) -> dict:
#     """
#     最终整合：
#     读取主状态中所有数据，生成最终输出
#     """
#     section_map = {}
#     for section in state.get('completed_sections', []):
#         key = f"{section['chapter_name']}|{section['section_name']}"
#         section_map[key] = section['content']
    
#     output = f"# {state['book_name']}\n\n"
#     output += f"主题：{state['topic']}\n\n"
    
#     for chapter in state.get('chapters', []):
#         output += f"## {chapter.name}\n\n"
#         output += f"{chapter.contents}\n\n"
        
#         for section in chapter.sections:
#             key = f"{chapter.name}|{section.name}"
#             content = section_map.get(key, section.contents)
#             output += f"### {section.name}\n\n"
#             output += f"{content}\n\n"
    
#     return {"final_output": output}

# sub_graph = StateGraph(Section_gene_State)
# sub_graph.add_node("llm_call_gene_section", llm_call_gene_section)
# sub_graph.add_node("evaluator_for_section", evaluator_for_section)
# sub_graph.set_entry_point("llm_call_gene_section")
# sub_graph.add_edge("llm_call_gene_section", "evaluator_for_section")
# sub_graph.add_conditional_edges("evaluator_for_section", router_section, {
#     "pass": END,
#     "refuse": "llm_call_gene_section"
# })

# graph = StateGraph(Creative_writing_State)

# graph.add_node("orchestrator", orchestrator)
# graph.add_node("llm_call_gene_chapter", llm_call_gene_chapter)
# graph.add_node("sub_graph", sub_graph.compile())
# graph.add_node("chapter_combine", chapter_combine)
# graph.add_node("conbine", conbine)

# graph.set_entry_point("orchestrator")
# graph.add_conditional_edges("orchestrator", send_task_chapter, ["llm_call_gene_chapter"])
# graph.add_conditional_edges("llm_call_gene_chapter", send_task_section, ["sub_graph"])
# graph.add_edge("sub_graph", "chapter_combine")
# graph.add_edge("chapter_combine", "conbine")
# app = graph.compile()

# if __name__ == "__main__":
    
#     # 执行示例
#     result = app.invoke({
#         "book_name": "Python数据分析从入门到精通",
#         "topic": "使用Python进行数据分析和数据可视化",
#         # 这些字段会被 operator.add 自动初始化
#         "completed_chapters": [],
#         "completed_sections": []
#     })
    
#     # 打印结果
#     print("=" * 80)
#     print("最终输出:")
#     print(result.get("final_output", "未生成内容"))
    
#     # 查看中间状态
#     print("\n" + "=" * 80)
#     print(f"生成的章数量: {len(result.get('completed_chapters', []))}")
#     print(f"生成的节数量: {len(result.get('completed_sections', []))}")














from __future__ import annotations
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from typing import Literal, Annotated, TypedDict
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
import operator

model_name = "qwen2.5:7b-instruct-q4_K_M"
model = ChatOllama(model=model_name)

# 1. 数据模型：按引用顺序定义
class Section(BaseModel):
    name: str = Field(description="这一节的标题或名称。")
    contents: str = Field(description="这一节的概要内容。")

class Chapter(BaseModel):
    name: str = Field(description="这一章的标题或名称。")
    contents: str = Field(description="这一章的概要内容。")
    sections: list[Section] = Field(description="本章下的所有节内容。")

class Book(BaseModel):
    chapters: list[Chapter] = Field(description="本书下的所有章内容。")

planner = model.with_structured_output(Book)

class Evaluation(BaseModel):
    evals: Literal["pass", "refuse"] = Field(description="评判本节内容是否与节主题符合。")
    rewrite_advice: str = Field(description="改进建议。")

evaluator = model.with_structured_output(Evaluation)

MAX_RETRY = 3

# 2. 主图状态：主图里所有节点/边用到的键都放这里
class CreativeWritingState(TypedDict):
    book_name: str
    topic: str
    chapters: list[Chapter] | None
    chapter: Chapter                          # 当前章（由 Send 传入，逐分支独立）
    # 聚合字段
    completed_chapters: Annotated[list, operator.add]   # [{chapter_name, content}]
    completed_sections: Annotated[list, operator.add]   # [{chapter_name, section_name, content}]
    # 输出
    final_output: str

# 3. 节子图状态
class SectionState(TypedDict):
    chapter_name: str
    section: Section
    section_result: str
    evals: Literal["pass", "refuse"]
    rewrite_advice: str
    retry_count: int
    completed_sections: Annotated[list, operator.add]   # 与主图同名，用于回流

# ============ 主图节点 ============
def orchestrator(state: CreativeWritingState) -> dict:
    system_prompt = (
        "根据用户提出的主题，生成结构化的报告内容。"
        "要求逻辑严谨，章与章之间相互关联。每章不少于2节、不多于5节。"
    )
    report_gene_prompt = f"主题：{state['topic']}，书名：{state['book_name']}，创作其下的章节。"
    result = planner.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])
    return {"chapters": result.chapters}

def generate_chapter(state: CreativeWritingState) -> dict:
    chapter = state["chapter"]
    system_prompt = "根据已有的章名与内容，补充与完善章概要的设计。"
    report_gene_prompt = f"当前章名是：{chapter.name}，章概要是：{chapter.contents}，请完善。"
    result = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])
    # 直接聚合章内容（带章名），并保留 chapter 供后续分发节任务
    return {
        "completed_chapters": [{"chapter_name": chapter.name, "content": result.content}],
        "chapter": chapter,
    }

def send_task_chapter(state: CreativeWritingState) -> list[Send]:
    return [Send("generate_chapter", {"chapter": c}) for c in state["chapters"]]

def send_task_section(state: CreativeWritingState) -> list[Send]:
    chapter = state["chapter"]
    return [
        Send("section_subgraph", {"chapter_name": chapter.name, "section": s})
        for s in chapter.sections
    ]

def combine(state: CreativeWritingState) -> dict:
    chapter_map = {c["chapter_name"]: c["content"] for c in state.get("completed_chapters", [])}
    section_map = {}
    for s in state.get("completed_sections", []):
        section_map[f"{s['chapter_name']}|{s['section_name']}"] = s["content"]

    output = f"# {state['book_name']}\n\n主题：{state['topic']}\n\n"
    for chapter in state.get("chapters", []):
        output += f"## {chapter.name}\n\n"
        output += f"{chapter_map.get(chapter.name, chapter.contents)}\n\n"
        for section in chapter.sections:
            key = f"{chapter.name}|{section.name}"
            output += f"### {section.name}\n\n"
            output += f"{section_map.get(key, section.contents)}\n\n"
    return {"final_output": output}

# ============ 节子图节点 ============
def generate_section(state: SectionState) -> dict:
    system_prompt = "根据已有的节信息，设计本节内容的核心。"
    report_gene_prompt = (
        f"当前章名是：{state['chapter_name']}，节名是：{state['section'].name}，"
        f"节概要是：{state['section'].contents}，请设计本节的核心内容。"
    )
    retry = state.get("retry_count", 0)
    if state.get("evals") == "refuse":
        system_prompt += f"根据主编的建议改进并重写：{state['rewrite_advice']}。"
        retry += 1
    result = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])
    return {"section_result": result.content, "retry_count": retry}

def evaluate_section(state: SectionState) -> dict:
    system_prompt = "你是资深主编，评判节内容是否与节主题符合，输出 evals 和 rewrite_advice。"
    report_gene_prompt = f"节名：{state['section'].name}，内容：{state['section_result']}，请评判。"
    grade = evaluator.invoke([SystemMessage(content=system_prompt), HumanMessage(content=report_gene_prompt)])
    return {"evals": grade.evals, "rewrite_advice": grade.rewrite_advice}

def collect_section(state: SectionState) -> dict:
    return {
        "completed_sections": [{
            "chapter_name": state["chapter_name"],
            "section_name": state["section"].name,
            "content": state["section_result"],
        }]
    }

def route_section(state: SectionState) -> str:
    if state.get("evals") == "pass":
        return "collect"
    if state.get("retry_count", 0) >= MAX_RETRY:
        return "collect"
    return "generate"

# ============ 构建图 ============
section_graph = StateGraph(SectionState)
section_graph.add_node("generate", generate_section)
section_graph.add_node("evaluate", evaluate_section)
section_graph.add_node("collect", collect_section)
section_graph.set_entry_point("generate")
section_graph.add_edge("generate", "evaluate")
section_graph.add_conditional_edges("evaluate", route_section, {"generate": "generate", "collect": "collect"})
section_graph.add_edge("collect", END)
sub_graph = section_graph.compile()

graph = StateGraph(CreativeWritingState)
graph.add_node("orchestrator", orchestrator)
graph.add_node("generate_chapter", generate_chapter)
graph.add_node("section_subgraph", sub_graph)
graph.add_node("combine", combine)

graph.set_entry_point("orchestrator")
graph.add_conditional_edges("orchestrator", send_task_chapter, ["generate_chapter"])
graph.add_conditional_edges("generate_chapter", send_task_section, ["section_subgraph"])
graph.add_edge("section_subgraph", "combine")
graph.add_edge("combine", END)
app = graph.compile()

if __name__ == "__main__":
    result = app.invoke({
        "book_name": "Python数据分析从入门到精通",
        "topic": "使用Python进行数据分析和数据可视化",
        "completed_chapters": [],
        "completed_sections": [],
    })
    print(result.get("final_output", "未生成内容"))