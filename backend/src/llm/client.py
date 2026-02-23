"""LLM client using LangChain for DeepSeek"""

from typing import Any
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel

from src.config import settings
from src.core.logging import log
from src.llm.types import LLMResponse, ToolCall


class LLMClient:
    """Unified LLM client using LangChain."""

    def __init__(self, model: str | None = None, provider: str | None = None):
        self.model_name = model or settings.DEFAULT_LLM_MODEL
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self._client: BaseChatModel | None = None

    @property
    def client(self) -> BaseChatModel:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> BaseChatModel:
        log.debug(f"Creating LLM client: provider={self.provider}, model={self.model_name}")

        if self.provider == "deepseek":
            return init_chat_model(
                model=self.model_name,
                model_provider="openai",
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            )
        elif self.provider == "openai":
            return init_chat_model(
                model=self.model_name,
                model_provider="openai",
                api_key=settings.get("OPENAI_API_KEY", ""),
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list:
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                if msg.get("tool_calls"):
                    lc_tool_calls = []
                    for tc in msg["tool_calls"]:
                        if "function" in tc:
                            lc_tool_calls.append({
                                "id": tc.get("id", ""),
                                "name": tc["function"].get("name", ""),
                                "args": tc["function"].get("arguments", {}),
                            })
                        else:
                            lc_tool_calls.append(tc)
                    lc_messages.append(AIMessage(content=content or "", tool_calls=lc_tool_calls))
                else:
                    lc_messages.append(AIMessage(content=content))
            elif role == "tool":
                lc_messages.append(ToolMessage(
                    content=content,
                    tool_call_id=msg.get("tool_call_id", ""),
                ))
        return lc_messages

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        lc_messages = self._convert_messages(messages)
        kwargs: dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        client = self.client
        if tools:
            client = client.bind_tools(tools)

        try:
            response = await client.ainvoke(lc_messages, **kwargs)

            tool_calls = None
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.get("id", ""),
                        name=tc.get("name", ""),
                        arguments=tc.get("args", {}),
                    )
                    for tc in response.tool_calls
                ]

            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "input_tokens": response.usage_metadata.get("input_tokens", 0),
                    "output_tokens": response.usage_metadata.get("output_tokens", 0),
                }

            return LLMResponse(
                content=response.content if isinstance(response.content, str) else None,
                tool_calls=tool_calls,
                usage=usage,
                model=self.model_name,
            )

        except Exception as e:
            log.error(f"LLM request failed: {e}")
            raise


@lru_cache()
def get_llm_client(
    model: str | None = None,
    provider: str | None = None,
) -> LLMClient:
    return LLMClient(model=model, provider=provider)
