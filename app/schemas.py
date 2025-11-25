from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool


class TeamCreate(BaseModel):
    team_name: str
    members: List[TeamMember]


class TeamResponse(BaseModel):
    team_name: str
    members: List[TeamMember]


class UserResponse(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool


class UserSetActive(BaseModel):
    user_id: str
    is_active: bool


class PullRequestCreate(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class PullRequestResponse(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    assigned_reviewers: List[str]
    createdAt: Optional[datetime] = None
    mergedAt: Optional[datetime] = None


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str


class PullRequestMerge(BaseModel):
    pull_request_id: str


class PullRequestReassign(BaseModel):
    pull_request_id: str
    old_user_id: str


class ReassignResponse(BaseModel):
    pr: PullRequestResponse
    replaced_by: str


class UserReviewResponse(BaseModel):
    user_id: str
    pull_requests: List[PullRequestShort]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class StatsResponse(BaseModel):
    total_prs: int
    open_prs: int
    merged_prs: int
    total_users: int
    active_users: int
    total_teams: int
    reviewer_assignments: dict[str, int]  # user_id -> count


class BulkDeactivateRequest(BaseModel):
    team_name: str

