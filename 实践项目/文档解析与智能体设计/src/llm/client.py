from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from config.setting import get_settings

settings = get_settings()


class LLMClient:
    """LLM 客户端，封装模型初始化、对话与结构化输出"""

    def __init__(self, model_name: str = None, base_url: str = None, temperature: float = None):
        # 默认使用对话模型；结构化提取等场景可传入主力模型
        self.model_name = model_name or f"{settings.model_provider}:{settings.chat_model}"
        self.base_url = base_url or settings.local_base_url
        self.temperature = temperature if temperature is not None else settings.temperature

    def get_llm(self) -> BaseChatModel:
        """
        获取 LLM 模型实例
        """
        try:
            return init_chat_model(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
            )
        except Exception:
            # 指定模型加载失败，降级到本地主力模型
            fallback = f"{settings.model_provider}:{settings.main_model}"
            return init_chat_model(
                model=fallback,
                base_url=settings.local_base_url,
                temperature=self.temperature,
            )

    def simple_chat(self, prompt: str) -> str:
        """
        简单的聊天接口
        """
        llm = self.get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    def structured_chat(self, prompt: str, schema):
        """
        结构化输出接口：让 LLM 输出符合 schema 的对象
        """
        llm = self.get_llm()
        structured_llm = llm.with_structured_output(schema)
        return structured_llm.invoke([HumanMessage(content=prompt)])


if __name__ == "__main__":
    client = LLMClient()
    llm = client.get_llm()
    print(type(llm))
