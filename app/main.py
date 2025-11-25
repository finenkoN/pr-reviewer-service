from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, services, exceptions

app = FastAPI(
    title="PR Reviewer Assignment Service",
    version="1.0.0",
    description="Service for assigning reviewers to Pull Requests"
)


@app.exception_handler(exceptions.ServiceException)
async def service_exception_handler(request, exc: exceptions.ServiceException):
    status_code = 400
    if exc.code == "NOT_FOUND":
        status_code = 404
    elif exc.code in ["PR_EXISTS", "TEAM_EXISTS", "PR_MERGED", "NOT_ASSIGNED", "NO_CANDIDATE"]:
        status_code = 409 if exc.code in ["PR_EXISTS", "TEAM_EXISTS", "PR_MERGED", "NOT_ASSIGNED", "NO_CANDIDATE"] else 400

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/team/add", response_model=schemas.TeamResponse, status_code=201)
async def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    """Create team with members (creates/updates users)"""
    team_obj = services.create_team(
        db,
        team.team_name,
        [{"user_id": m.user_id, "username": m.username, "is_active": m.is_active} for m in team.members]
    )

    return schemas.TeamResponse(
        team_name=team_obj.team_name,
        members=[
            schemas.TeamMember(
                user_id=user.user_id,
                username=user.username,
                is_active=user.is_active
            )
            for user in team_obj.members
        ]
    )


@app.get("/team/get", response_model=schemas.TeamResponse)
async def get_team(team_name: str = Query(..., description="Уникальное имя команды"), db: Session = Depends(get_db)):
    """Get team with members"""
    team = services.get_team_by_name(db, team_name)

    return schemas.TeamResponse(
        team_name=team.team_name,
        members=[
            schemas.TeamMember(
                user_id=user.user_id,
                username=user.username,
                is_active=user.is_active
            )
            for user in team.members
        ]
    )


@app.post("/users/setIsActive", response_model=schemas.UserResponse)
async def set_user_active(request: schemas.UserSetActive, db: Session = Depends(get_db)):
    """Set user active flag"""
    user = services.set_user_active(db, request.user_id, request.is_active)

    return schemas.UserResponse(
        user_id=user.user_id,
        username=user.username,
        team_name=user.team_name,
        is_active=user.is_active
    )


@app.post("/pullRequest/create", response_model=schemas.PullRequestResponse, status_code=201)
async def create_pull_request(pr: schemas.PullRequestCreate, db: Session = Depends(get_db)):
    """Create PR and automatically assign up to 2 reviewers from author's team"""
    pr_obj = services.create_pull_request(
        db,
        pr.pull_request_id,
        pr.pull_request_name,
        pr.author_id
    )

    return schemas.PullRequestResponse(
        pull_request_id=pr_obj.pull_request_id,
        pull_request_name=pr_obj.pull_request_name,
        author_id=pr_obj.author_id,
        status=pr_obj.status,
        assigned_reviewers=[r.user_id for r in pr_obj.assigned_reviewers],
        createdAt=pr_obj.created_at,
        mergedAt=pr_obj.merged_at
    )


@app.post("/pullRequest/merge", response_model=schemas.PullRequestResponse)
async def merge_pull_request(request: schemas.PullRequestMerge, db: Session = Depends(get_db)):
    """Mark PR as MERGED (idempotent operation)"""
    pr = services.merge_pull_request(db, request.pull_request_id)

    return schemas.PullRequestResponse(
        pull_request_id=pr.pull_request_id,
        pull_request_name=pr.pull_request_name,
        author_id=pr.author_id,
        status=pr.status,
        assigned_reviewers=[r.user_id for r in pr.assigned_reviewers],
        createdAt=pr.created_at,
        mergedAt=pr.merged_at
    )


@app.post("/pullRequest/reassign", response_model=schemas.ReassignResponse)
async def reassign_reviewer(request: schemas.PullRequestReassign, db: Session = Depends(get_db)):
    """Reassign specific reviewer to another from their team"""
    pr, new_reviewer_id = services.reassign_reviewer(
        db,
        request.pull_request_id,
        request.old_user_id
    )

    return schemas.ReassignResponse(
        pr=schemas.PullRequestResponse(
            pull_request_id=pr.pull_request_id,
            pull_request_name=pr.pull_request_name,
            author_id=pr.author_id,
            status=pr.status,
            assigned_reviewers=[r.user_id for r in pr.assigned_reviewers],
            createdAt=pr.created_at,
            mergedAt=pr.merged_at
        ),
        replaced_by=new_reviewer_id
    )


@app.get("/users/getReview", response_model=schemas.UserReviewResponse)
async def get_user_reviews(user_id: str = Query(..., description="Идентификатор пользователя"), db: Session = Depends(get_db)):
    """Get PRs where user is assigned as reviewer"""
    prs = services.get_user_reviews(db, user_id)

    return schemas.UserReviewResponse(
        user_id=user_id,
        pull_requests=[
            schemas.PullRequestShort(
                pull_request_id=pr.pull_request_id,
                pull_request_name=pr.pull_request_name,
                author_id=pr.author_id,
                status=pr.status
            )
            for pr in prs
        ]
    )


# Additional endpoints

@app.get("/stats", response_model=schemas.StatsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """Get service statistics"""
    stats = services.get_statistics(db)
    return schemas.StatsResponse(**stats)


@app.post("/users/bulkDeactivate", status_code=200)
async def bulk_deactivate_team(request: schemas.BulkDeactivateRequest, db: Session = Depends(get_db)):
    """Bulk deactivate team members and safely reassign open PRs"""
    reassigned_count = services.bulk_deactivate_team(db, request.team_name)
    return {
        "team_name": request.team_name,
        "reassigned_prs": reassigned_count,
        "message": f"Team members deactivated. {reassigned_count} PRs reassigned."
    }

