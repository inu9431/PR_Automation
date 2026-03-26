from sqlalchemy.orm import Session
from app.models.cost_log import CostLog

def log_cost(db: Session, pr_number: int, input_tokens: int, output_tokens: int, cost: float):
    entry = CostLog(
        pr_number=pr_number,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=round(cost, 6),
        cost_krw=round(cost * 1400, 2),
    )
    db.add(entry)
    db.commit()

def get_total_cost(db: Session) -> dict:
    logs = db.query(CostLog).all()
    total_usd = sum(log.cost_usd for log in logs)

    return {
        "total_pr_count": len(logs),
        "total_cost_usd": round(total_usd, 6),
        "total_cost_krw": round(total_usd * 1400, 2),
    }