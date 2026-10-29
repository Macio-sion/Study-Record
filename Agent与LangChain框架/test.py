"""
股票信息查询工具集 + Agent 短时记忆示例

功能：
1. get_current_date — 获取系统当前日期
2. query_stock_code — 根据公司名称查询股票代码
3. query_stock_info — 查询近三个月的股票交易数据

设计要点：
- 每个工具使用 args_schema（Pydantic BaseModel）定义标准输入
- 每个工具使用 response_format（Pydantic BaseModel）定义标准输出格式
- 使用 create_agent 实现带短时记忆的智能体
- 返回结构化 JSON 而非原始 DataFrame
- 完善的错误处理
"""

import time
import json
from datetime import datetime, timedelta
from typing import Optional, List

import tushare as ts
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage
from langchain_core.tools import tool


# ============================================================================
# 1. 输出格式模型（response_format）
# ============================================================================

class StockCodeOutput(BaseModel):
    """查询股票代码的返回格式"""
    stock_name: str = Field(description="公司/股票名称")
    ts_code: str = Field(description="股票代码（如 000001.SZ）")
    symbol: str = Field(description="股票简称代码")
    area: str = Field(description="所属地区")
    industry: str = Field(description="所属行业")
    list_date: str = Field(description="上市日期")


class DailyItem(BaseModel):
    """单日交易数据项"""
    trade_date: str = Field(description="交易日期（YYYYMMDD）")
    open: float = Field(description="开盘价")
    high: float = Field(description="最高价")
    low: float = Field(description="最低价")
    close: float = Field(description="收盘价")
    change: float = Field(description="涨跌额")
    pct_chg: float = Field(description="涨跌幅(%)")
    amount: float = Field(description="成交额(千元)")
    vol: float = Field(description="成交量(手)")


class StockInfoOutput(BaseModel):
    """查询股票交易数据的返回格式"""
    stock_code: str = Field(description="股票代码")
    query_start: str = Field(description="查询起始日期")
    query_end: str = Field(description="查询结束日期")
    total_records: int = Field(description="数据总条数")
    data: List[DailyItem] = Field(description="交易数据列表")


# ============================================================================
# 2. 输入参数模型（args_schema）
# ============================================================================

class QueryStockCodeInput(BaseModel):
    """查询股票代码的输入参数"""
    company_name: str = Field(
        description="公司名称，如'平安银行'、'万科A'等"
    )
    pro_api: str = Field(
        description="tushare pro 的 API token"
    )


class QueryStockInfoInput(BaseModel):
    """查询股票交易数据的输入参数"""
    stock_code: str = Field(
        description="股票代码，如 000001.SZ"
    )
    current_date: str = Field(
        description="当前日期，格式 YYYYMMDD，如 20240820"
    )
    pro_api: str = Field(
        description="tushare pro 的 API token"
    )


# ============================================================================
# 3. 工具函数定义
# ============================================================================

@tool(
    description="获取系统的当前日期，返回格式为 YYYYMMDD"
)
def get_current_date() -> str:
    """
    获取系统的当前日期。
    
    Returns:
        str: 当前日期，格式 YYYYMMDD
    """
    try:
        time_struct = time.localtime()
        current = time.strftime("%Y%m%d", time_struct)
        print(f"[get_current_date] 当前日期: {current}")
        return current
    except Exception as e:
        return json.dumps({"error": f"获取当前日期失败: {str(e)}"}, ensure_ascii=False)


@tool(
    args_schema=QueryStockCodeInput,
    response_format=StockCodeOutput,
    description="根据公司名称查询其在A股的股票代码及基本信息"
)
def query_stock_code(company_name: str, pro_api: str) -> str:
    """
    查询指定公司名称对应的股票代码和基本信息。
    使用 args_schema 定义标准输入，response_format 定义标准输出格式。

    Args:
        company_name: 公司名称，如 '平安银行'
        pro_api: tushare pro 的 API token

    Returns:
        str: JSON 格式的股票基本信息
    """
    print(f"[query_stock_code] 查询公司: {company_name}")
    try:
        pro = ts.pro_api(pro_api)
        df = pro.stock_basic(
            name=company_name,
            fields='ts_code,symbol,name,area,industry,list_date'
        )

        if df is None or len(df) == 0:
            return json.dumps({
                "error": f"未找到公司 '{company_name}' 的股票信息"
            }, ensure_ascii=False)

        # 取第一条匹配记录
        row = df.iloc[0]
        result = StockCodeOutput(
            stock_name=str(row.get("name", company_name)),
            ts_code=str(row.get("ts_code", "")),
            symbol=str(row.get("symbol", "")),
            area=str(row.get("area", "")),
            industry=str(row.get("industry", "")),
            list_date=str(row.get("list_date", "")),
        )
        print(f"[query_stock_code] 结果: {result.ts_code}")
        return result.model_dump_json(ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"查询股票代码失败: {str(e)}"
        }, ensure_ascii=False)


@tool(
    args_schema=QueryStockInfoInput,
    response_format=StockInfoOutput,
    description="查询指定股票代码近三个月的日线交易数据，包括开盘价、收盘价、涨跌幅等"
)
def query_stock_info(stock_code: str, current_date: str, pro_api: str) -> str:
    """
    查询指定股票代码近三个月的日线交易数据。
    使用 args_schema 定义标准输入，response_format 定义标准输出格式。

    Args:
        stock_code: 股票代码，如 '000001.SZ'
        current_date: 当前日期，格式 YYYYMMDD
        pro_api: tushare pro 的 API token

    Returns:
        str: JSON 格式的股票交易数据列表
    """
    print(f"[query_stock_info] 股票: {stock_code}, 截止日期: {current_date}")
    try:
        # 解析日期
        try:
            dt = datetime.strptime(current_date, "%Y%m%d")
        except ValueError:
            dt = datetime.strptime(current_date, "%Y-%m-%d")

        current_date_fmt = dt.strftime("%Y%m%d")

        # 计算三个月前的日期
        three_months_ago = dt - relativedelta(months=3)
        start_date = three_months_ago.strftime("%Y%m%d")

        # 查询数据
        pro = ts.pro_api(pro_api)
        df = pro.daily(
            ts_code=stock_code,
            start_date=start_date,
            end_date=current_date_fmt
        )

        if df is None or len(df) == 0:
            return json.dumps({
                "error": f"未查询到股票 {stock_code} 在 {start_date}~{current_date_fmt} 的交易数据"
            }, ensure_ascii=False)

        # 转换为结构化数据
        data_list: List[DailyItem] = []
        for _, row in df.iterrows():
            data_list.append(DailyItem(
                trade_date=str(row.get("trade_date", "")),
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                change=float(row.get("change", 0)),
                pct_chg=float(row.get("pct_chg", 0)),
                amount=float(row.get("amount", 0)),
                vol=float(row.get("vol", 0)),
            ))

        result = StockInfoOutput(
            stock_code=stock_code,
            query_start=start_date,
            query_end=current_date_fmt,
            total_records=len(data_list),
            data=data_list,
        )
        print(f"[query_stock_info] 查询到 {len(data_list)} 条记录")
        return result.model_dump_json(ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"查询股票交易数据失败: {str(e)}"
        }, ensure_ascii=False)


# ============================================================================
# 4. Agent 封装（带短时记忆）
# ============================================================================

class StockAgent:
    """股票查询智能体，封装 Agent 创建与短时记忆管理。

    特性：
    - 短时记忆：自动维护对话历史（HumanMessage / AIMessage）
    - 工具调用：自动选择并调用合适的工具
    - 流式输出：支持 stream_events 流式问答
    - 记忆管理：支持清空历史、查看历史条数

    Attributes:
        _agent: LangChain agent 实例（懒加载）。
        _history: 对话消息历史列表。
        _model_name: 模型名称。
        _tools: 工具列表。
        _system_prompt: 系统提示词。
    """

    def __init__(
        self,
        model_name: str = "ollama:qwen3.5:0.8b",
        tools: Optional[list] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """初始化股票查询智能体。

        Args:
            model_name: LangChain 模型标识符，如 'ollama:qwen3.5:0.8b'
            tools: 工具函数列表，默认使用股票查询工具集
            system_prompt: 自定义系统提示词
        """
        self._model_name = model_name
        self._tools = tools or [
            get_current_date,
            query_stock_code,
            query_stock_info,
        ]
        self._system_prompt = system_prompt or (
            "你是一个股票数据查询助手。你可以帮助用户：\n"
            "1. 获取当前日期\n"
            "2. 根据公司名称查询股票代码\n"
            "3. 查询指定股票近三个月的交易数据\n\n"
            "使用规则：\n"
            "- 查询股票数据前，必须先通过 query_stock_code 获取股票代码\n"
            "- 查询交易数据前，必须先通过 get_current_date 获取当前日期\n"
            "- 返回数据后，用中文清晰地展示和分析数据\n"
            "- 工具返回的 JSON 数据需要解析后展示给用户"
        )
        self._agent: Optional[object] = None
        self._history: list = []

    @property
    def agent(self):
        """懒加载创建 Agent 实例。"""
        if self._agent is None:
            print(f"[StockAgent] 创建 Agent: model={self._model_name}, tools={len(self._tools)}")
            self._agent = create_agent(
                model=self._model_name,
                tools=self._tools,
                system_prompt=self._system_prompt,
            )
        return self._agent

    def ask(self, question: str) -> str:
        """同步问答：发送问题，返回完整回答文本。

        自动维护对话历史（短时记忆），后续调用可参考之前的对话内容。

        Args:
            question: 用户输入文本。

        Returns:
            AI 回答的文本内容。
        """
        if not question.strip():
            return ""

        print(f"\n{'='*60}")
        print(f"[StockAgent] 用户: {question[:80]}...")
        self._history.append(HumanMessage(content=question))

        try:
            result = self.agent.invoke({"messages": self._history})
        except Exception as e:
            print(f"[StockAgent] 调用失败: {e}")
            return f"查询失败: {str(e)}"

        messages = result.get("messages", [])
        answer = self._extract_text(messages)
        self._history = messages  # 更新历史 → 短时记忆

        print(f"[StockAgent] AI: {answer[:100]}..." if len(answer) > 100 else f"[StockAgent] AI: {answer}")
        return answer

    def stream_ask(self, question: str):
        """流式问答生成器：逐步产出结构化事件。

        产出的事件类型：
        - {"type": "text", "content": "..."}  — 文本增量
        - {"type": "tool_call", "tool_name": "...", "args": {...}} — 工具调用
        - {"type": "tool_result", "tool_name": "...", "result": "..."} — 工具结果
        - {"type": "error", "message": "..."} — 错误
        - {"type": "done"} — 流结束

        Args:
            question: 用户输入文本。

        Yields:
            dict: 结构化事件字典。
        """
        if not question.strip():
            yield {"type": "done"}
            return

        print(f"\n{'='*60}")
        print(f"[StockAgent-Stream] 用户: {question[:80]}...")
        self._history.append(HumanMessage(content=question))

        try:
            for event in self.agent.stream_events(
                {"messages": self._history},
                version="v3",
            ):
                method = event.get("method", "")
                params = event.get("params", {})
                data = params.get("data", {})

                if method == "messages":
                    yield from self._parse_stream_event(data)
                elif method == "values":
                    yield from self._parse_values_event(data)

            yield {"type": "done"}
        except Exception as e:
            print(f"[StockAgent-Stream] 流式调用失败: {e}")
            yield {"type": "error", "message": str(e)}
            yield {"type": "done"}

    def _parse_stream_event(self, data):
        """解析流式事件数据。"""
        if not isinstance(data, tuple) or len(data) < 1:
            return
        event_dict = data[0]
        if not isinstance(event_dict, dict):
            return

        event_name = event_dict.get("event", "")
        if event_name == "content-block-delta":
            delta = event_dict.get("delta", {})
            delta_type = delta.get("type", "")
            if delta_type == "text-delta":
                text = delta.get("text", "")
                if text:
                    yield {"type": "text", "content": text}
        elif event_name == "content-block-start":
            content = event_dict.get("content", {})
            if content.get("type") == "tool_use":
                yield {
                    "type": "tool_call",
                    "tool_name": content.get("name", "unknown"),
                    "args": content.get("input", {}),
                }

    def _parse_values_event(self, data):
        """解析 values 事件，提取工具结果并更新历史。"""
        if isinstance(data, dict) and "messages" in data:
            self._history = data["messages"]
            for msg in self._history:
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        yield {
                            "type": "tool_result",
                            "tool_name": tc.get("name", ""),
                            "result": str(tc.get("result", "")),
                        }
        elif isinstance(data, tuple):
            for item in reversed(data):
                if isinstance(item, dict) and "messages" in item:
                    self._history = item["messages"]
                    break

    @staticmethod
    def _extract_text(messages: list) -> str:
        """从消息列表中提取最后一个 AIMessage 的文本内容。"""
        for msg in reversed(messages):
            if not isinstance(msg, AIMessage):
                continue
            content = msg.content
            if not content:
                continue
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                return "".join(parts)
            if isinstance(content, str):
                return content
        return ""

    def clear_history(self) -> None:
        """清空对话历史，重置短时记忆。"""
        self._history = []
        print("[StockAgent] 对话历史已清空")

    @property
    def history_count(self) -> int:
        """获取当前对话历史的消息数量。"""
        return len(self._history)

    @property
    def history(self) -> list:
        """获取对话历史（只读）。"""
        return list(self._history)


# ============================================================================
# 5. 主程序入口
# ============================================================================

if __name__ == "__main__":
    # 你的 tushare token
    TUSHARE_TOKEN = "cf8c570c7475d05a5ed12474997859b1ee4e17f85a4cc2ec3050610a"

    # 创建带短时记忆的 Agent
    agent = StockAgent(
        model_name="ollama:qwen3.5:0.8b",
    )

    print("=" * 60)
    print("股票查询智能体（带短时记忆）")
    print("=" * 60)

    # 测试1：第一轮对话 — 查询股票代码
    question1 = (
        f"我的平台API_token是'{TUSHARE_TOKEN}'，"
        "请帮我查询平安银行的股票代码。"
    )
    print("\n>>> 第一轮对话 <<<")
    answer1 = agent.ask(question1)
    print(f"\n📝 AI 回答:\n{answer1}")

    # 验证短时记忆：此时 history 应该有 2+ 条消息
    print(f"\n📊 当前历史消息数: {agent.history_count}")

    # 测试2：第二轮对话 — 利用短时记忆，查询近三个月交易数据
    # Agent 应该记得上一轮已经查到了平安银行的股票代码
    question2 = (
        f"我的平台API_token是'{TUSHARE_TOKEN}'，"
        "请帮我查询近三个月的股票交易数据，并展示分析。"
    )
    print("\n>>> 第二轮对话（利用短时记忆）<<<")
    answer2 = agent.ask(question2)
    print(f"\n📝 AI 回答:\n{answer2}")

    print(f"\n📊 最终历史消息数: {agent.history_count}")
    print("\n✅ 测试完成！短时记忆使得第二轮对话可以引用第一轮的结果。")