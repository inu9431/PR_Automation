import hashlib
import hmac
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.config import settings
from app.schemas.github import WebhookPayload, CostSummaryResponse
from app.services.reviewer import review_pr
from app.services.cost_logger import get_total_cost
from app.database import get_db, SessionLocal

logger = logging.getLogger(__name__)


def verify_signature(body: bytes, signature_header: str) -> bool:
    expected = "sha256=" + hmac.new(
        key=settings.github_webhook_secret.encode(),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


async def run_review_in_background(repo, pr_number, pr_title, pr_url, author):
    db = SessionLocal()
    try:
        await review_pr(repo, pr_number, pr_title, pr_url, author, db)
    finally:
        db.close()


router = APIRouter()


@router.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(default=None),
):
    body = await request.body()

    if not x_hub_signature_256:
        logger.warning("Webhook 서명 헤더 누락")
        raise HTTPException(status_code=401, detail="서명 헤더 누락")

    if not verify_signature(body, x_hub_signature_256):
        logger.warning("Webhook 서명 불일치")
        raise HTTPException(status_code=401, detail="서명 불일치")

    try:
        data = await request.json()
    except Exception:
        logger.error("Webhook payload JSON 파싱 실패")
        return {"status": "error", "message": "잘못된 JSON 형식"}

    if data.get("action") != "opened":
        return {"status": "skipped"}

    try:
        payload = WebhookPayload.model_validate(data)
    except ValidationError as e:
        logger.error(f"Webhook payload 형식 오류: {e}")
        return {"status": "error", "message": "필수 데이터 누락"}

    background_tasks.add_task(
        run_review_in_background,
        repo=payload.repository.full_name,
        pr_number=payload.pull_request.number,
        pr_title=payload.pull_request.title,
        pr_url=payload.pull_request.html_url,
        author=payload.pull_request.user.login,
    )

    return {"status": "ok"}

@router.get("/cost", response_model=CostSummaryResponse)
async def cost_summary(db: Session = Depends(get_db)):
    return get_total_cost(db)

