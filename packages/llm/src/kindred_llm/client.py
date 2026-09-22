from importlib.metadata import version

import httpx2
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

USER_AGENT = f"kindred/{version('kindred-llm')}"
# OpenCode routes and caches by conversation; other providers ignore it.
SESSION_HEADER = "x-opencode-session"


class LLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client,
            default_headers={"User-Agent": USER_AGENT},
        )
        self._model = model

    async def complete(
        self, prompt: str, *, session_id: str, system: str | None = None
    ) -> str:
        messages: list[ChatCompletionMessageParam] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            extra_headers={SESSION_HEADER: session_id},
        )
        return response.choices[0].message.content or ""
