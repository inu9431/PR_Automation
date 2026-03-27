import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session
from app.schemas.github import WebhookPayload, CostSummaryResponse
from app.services.reviewer import review_pr
from app.services.cost_logger import get_total_cost
from app.database import get_db, SessionLocal

logger = logging.getLogger(__name__)

async def run_review_in_background(repo, pr_number, pr_title, pr_url, author):
    db = SessionLocal()
    try:
        await review_pr(repo, pr_number, pr_title, pr_url, author, db)
    finally:
        db.close()
router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json() # github,webhook.payload 값을 json 파싱
    except Exception:
        logger.error("Webhook payload JSON 파싱 실패")
        return {"status": "error", "message": "잘못된 JSON 형식"}

    if data.get("action") != "opened": # pr이 열릴경우만 신호로 판단하고 나머지경우는 스킵
        return {"status": "skipped"}

    pr = data.get("pull_request", {}) # get 조회시 None일경우 에러발생하지만 빈 {}일 경우 에러가 발생하지않아서 빈값으로 처리
    repo_full_name = data.get("repository", {}).get("full_name") # 위랑 같은패턴
    pr_number = pr.get("number")

    if not repo_full_name or not pr_number:
        logger.error(f"필수 데이터 누락: repo={repo_full_name}, pr={pr_number}")
        return {"status": "error", "message": "필수 데이터 누락"}

    background_tasks.add_task(
        run_review_in_background,
        repo = repo_full_name,
        pr_number = pr_number,
        pr_title = pr.get("title"),
        pr_url = pr.get("html_url"),
        author = pr.get("user", {}).get("login"),
    )

    return {"status": "ok"}

@router.get("/cost", response_model=CostSummaryResponse)
async def cost_summary(db: Session = Depends(get_db)):
    return get_total_cost(db)

