import asyncio
import uuid

from kindred_api.config import get_settings
from kindred_llm import LLMClient


async def main() -> None:
    settings = get_settings()
    client = LLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key.get_secret_value(),
        model=settings.llm_model,
    )
    reply = await client.complete(
        "Say hello in five words.", session_id=str(uuid.uuid4())
    )
    print(reply)


if __name__ == "__main__":
    asyncio.run(main())
