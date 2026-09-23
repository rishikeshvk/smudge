import asyncio
import uuid

from kindred_api.config import get_settings
from kindred_api.llm_clients import build_llm


async def main() -> None:
    settings = get_settings()
    client = build_llm(settings, settings.llm_model_persona)
    reply = await client.complete(
        "Say hello in five words.", session_id=str(uuid.uuid4())
    )
    print(reply)


if __name__ == "__main__":
    asyncio.run(main())
