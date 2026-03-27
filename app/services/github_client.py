import httpx
from app.config import settings

HEADERS = {
    "Authorization": f"token {settings.github_token}",
    "Accept": "application/vnd.github.v3+json",
}

async def get_pr_diff_text(repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"

    async with httpx.AsyncClient() as client: # 비동기 처리를 위해 사용
        res = await client.get(url, headers=HEADERS) # 요청 보내고 받음
        res.raise_for_status() # 200일떄만 ok 나머지는 예외처리
        files = res.json() # 응답 데이터를 json

    result = []
    for f in files:
        filename = f["filename"] # 변경된 경로
        patch = f.get("patch", "(binary or no diff)") # diff 내용
        result.append(f"###{filename}\n```\n{patch}\n```") # 리스트 저장
    return "\n\n".join(result) # 변경된 값을 판단