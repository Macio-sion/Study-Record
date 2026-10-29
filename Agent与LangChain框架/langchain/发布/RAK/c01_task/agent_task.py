from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
"""
redis_agent_kit本质是将agent、llm的调用封装成Task(使用Redis管理的消息队列)，然后作为Web服务发布
"""
from redis_agent_kit import TaskContext

"""
要用async修饰做成协程，因为TaskContext是异步的
"""

async def langchain_agent(ctx: TaskContext) -> dict:
    """
    把langchain的agent、llm的调用封装成Task
    ctx: TaskContext对象，包含了任务的上下文信息。主要是与http的request与redis通信的上下文
    返回值: dict，包含了后端处理结果(所谓的数据接口)
    """
    await ctx.emitter.emit("初始化llm中")
    llm = init_chat_model(
        model="ollama:qwen3.5:0.8b"
    )
    await ctx.emitter.emit("初始化llm完成")
    await ctx.emitter.emit("初始化agent中")
    agent = create_agent(
        llm, 
        tools=[]
    )
    await ctx.emitter.emit("初始化agent完成")
    user_message = ctx.message
    result = await agent.ainvoke(HumanMessage(content=user_message))
    await ctx.emitter.emit("调用agent完成")
    
    # 这里数据返回给Redis队列，前端从Redis队列中获取数据
    return {
        "answer": result['messages'][-1].content
    }
