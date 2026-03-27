import httpx
from app.config import settings

async def send_discord_message(content: str):
    if len(content) > 2000: # 디스코드가 2000자 내라서 1990자로 제
        content = content[:1990] + "\n..."

    async with httpx.AsyncClient() as client: # 통신
        res = await client.post(
            settings.discord_webhook_url,
            json={"content": content}, # json post요청하면 메세지 전송
        )
        res.raise_for_status() # 200이면 ok 나머지 스킵
