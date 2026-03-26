import httpx
from app.config import settings

async def send_discord_message(content: str):
    if len(content) > 2000:
        content = content[:1990] + "\n..."

    async with httpx.AsyncClient() as client:
        res = await client.post(
            settings.discord_webhook_url,
            json={"content": content},
        )
        res.raise_for_status()
