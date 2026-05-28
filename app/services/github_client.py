import httpx

from app.config import settings

HEADERS = {
    "Authorization": f"token {settings.github_token}",
    "Accept": "application/vnd.github.v3+json",
}


async def get_pr_diff_text(repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
        res.raise_for_status()
        files = res.json()

    result = []
    for f in files:
        filename = f["filename"]
        patch = f.get("patch", "(binary or no diff)")
        result.append(f"###{filename}\n```\n{patch}\n```")
    return "\n\n".join(result)
