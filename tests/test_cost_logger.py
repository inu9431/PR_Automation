from unittest.mock import MagicMock
from app.services.cost_logger import log_cost, get_total_cost

def test_log_cost(db):
    log_cost(db, pr_number=1, input_tokens=1000, output_tokens=500, cost=0.0105)
    db.add.assert_called_once()
    db.commit.assert_called_once()

def test_get_total_cost_empty(db):
    db.query.return_value.all.return_value = []
    result = get_total_cost(db)
    assert result["total_pr_count"] == 0
    assert result["total_cost_usd"] == 0.0


def test_get_total_cost(db):
    db.query.return_value.all.return_value = [
        MagicMock(cost_usd=0.01),
        MagicMock(cost_usd=0.02),
    ]
    result = get_total_cost(db)
    assert result["total_pr_count"] == 2
    assert result["total_cost_usd"] == 0.03