from pydantic import BaseModel

class PRSchema(BaseModel):
    number: int
    title: str
    html_url: str
    user: dict

class WebhookPayload(BaseModel):
    action: str
    pull_request: PRSchema
    repository: dict

class CostSummaryResponse(BaseModel):
    total_pr_count: int
    total_cost_usd: float
    total_cost_krw: float
