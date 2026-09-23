import json
import re
from importlib.metadata import version

import httpx2
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError

USER_AGENT = f"kindred/{version('kindred-llm')}"
# OpenCode routes and caches by conversation; other providers ignore it.
SESSION_HEADER = "x-opencode-session"
STRUCTURED_ATTEMPTS = 3
FENCED = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class StructuredOutputError(Exception):
    pass


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
        self.model = model

    async def complete(
        self, prompt: str, *, session_id: str, system: str | None = None
    ) -> str:
        messages: list[ChatCompletionMessageParam] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self._chat(messages, session_id)

    async def complete_structured[T: BaseModel](
        self, schema: type[T], prompt: str, *, session_id: str, system: str
    ) -> T:
        # Open models vary in JSON reliability, so validate and feed errors back.
        contract = json.dumps(schema.model_json_schema())
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": f"{system}\n\nReply with only a JSON object matching "
                f"this JSON Schema:\n{contract}",
            },
            {"role": "user", "content": prompt},
        ]
        for _ in range(STRUCTURED_ATTEMPTS):
            reply = await self._chat(messages, session_id)
            try:
                return schema.model_validate_json(_json_text(reply))
            except ValidationError as error:
                messages += [
                    {"role": "assistant", "content": reply},
                    {
                        "role": "user",
                        "content": f"That reply was invalid:\n{error}\n"
                        "Reply again with only the corrected JSON object.",
                    },
                ]
        raise StructuredOutputError(
            f"{schema.__name__} still invalid after {STRUCTURED_ATTEMPTS} attempts"
        )

    async def _chat(
        self, messages: list[ChatCompletionMessageParam], session_id: str
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            extra_headers={SESSION_HEADER: session_id},
        )
        return response.choices[0].message.content or ""


def _json_text(reply: str) -> str:
    fenced = FENCED.search(reply)
    return fenced.group(1) if fenced else reply.strip()
