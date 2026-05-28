from pydantic import BaseModel


class UserSchema(BaseModel):
    login: str


class PRSchema(BaseModel):
    number: int
    title: str
    html_url: str
    user: UserSchema


class RepositorySchema(BaseModel):
    full_name: str


class WebhookPayload(BaseModel):
    action: str
    pull_request: PRSchema
    repository: RepositorySchema


class CostSummaryResponse(BaseModel):
    total_pr_count: int
    total_cost_usd: float
    total_cost_krw: float
