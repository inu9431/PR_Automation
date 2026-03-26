from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session
from app.schemas.github import WebhookPayload, CostSummaryResponse
from app.services.reviewer import review_pr
from app.services.cost_logger import get_total_cost
from app.database import get_db

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    data = await request.json()
    if data.get("action") != "opened":
        return {"status": "skipped"}
    pr = data.get("pull_request", {})

    repo_full_name = data.get("repository", {}).get("full_name")

    background_tasks.add_task(
        review_pr,
        repo = repo_full_name,
        pr_number = pr.get("number"),
        pr_title = pr.get("title"),
        pr_url = pr.get("html_url"),
        author = pr.get("user", {}).get("login"),
        db=db
    )

    return {"status": "ok"}

@router.get("/cost", response_model=CostSummaryResponse)
async def cost_summary(db: Session = Depends(get_db)):
    return get_total_cost(db)

