from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Team, User, PullRequest
from app.exceptions import (
    TeamExistsError,
    TeamNotFoundError,
    UserNotFoundError,
    PRExistsError,
    PRNotFoundError,
    PRMergedError,
    ReviewerNotAssignedError,
    NoCandidateError
)
import random
from typing import List


def get_team_by_name(db: Session, team_name: str) -> Team:
    team = db.query(Team).filter(Team.team_name == team_name).first()
    if not team:
        raise TeamNotFoundError(f"Team '{team_name}' not found")
    return team


def create_team(db: Session, team_name: str, members: List[dict]) -> Team:
    existing_team = db.query(Team).filter(Team.team_name == team_name).first()
    if existing_team:
        raise TeamExistsError(f"Team '{team_name}' already exists")

    team = Team(team_name=team_name)
    db.add(team)
    db.flush()

    for member_data in members:
        user = db.query(User).filter(User.user_id == member_data["user_id"]).first()
        if user:
            # Update existing user
            user.username = member_data["username"]
            user.is_active = member_data["is_active"]
            user.team_name = team_name
        else:
            # Create new user
            user = User(
                user_id=member_data["user_id"],
                username=member_data["username"],
                team_name=team_name,
                is_active=member_data["is_active"]
            )
            db.add(user)

    db.commit()
    db.refresh(team)
    return team


def get_user_by_id(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise UserNotFoundError(f"User '{user_id}' not found")
    return user


def set_user_active(db: Session, user_id: str, is_active: bool) -> User:
    user = get_user_by_id(db, user_id)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def get_active_reviewers_from_team(db: Session, team_name: str, exclude_user_id: str = None) -> List[User]:
    """Get active users from team, excluding specified user"""
    query = db.query(User).filter(
        and_(
            User.team_name == team_name,
            User.is_active == True
        )
    )
    if exclude_user_id:
        query = query.filter(User.user_id != exclude_user_id)
    return query.all()


def assign_reviewers(db: Session, author_id: str) -> List[str]:
    """Assign up to 2 active reviewers from author's team, excluding author"""
    author = get_user_by_id(db, author_id)
    candidates = get_active_reviewers_from_team(db, author.team_name, exclude_user_id=author_id)

    # Select up to 2 random reviewers
    num_reviewers = min(2, len(candidates))
    selected = random.sample(candidates, num_reviewers) if candidates else []

    return [user.user_id for user in selected]


def create_pull_request(
    db: Session,
    pull_request_id: str,
    pull_request_name: str,
    author_id: str
) -> PullRequest:
    # Check if PR already exists
    existing_pr = db.query(PullRequest).filter(
        PullRequest.pull_request_id == pull_request_id
    ).first()
    if existing_pr:
        raise PRExistsError(f"PR '{pull_request_id}' already exists")

    # Verify author exists
    author = get_user_by_id(db, author_id)

    # Create PR
    pr = PullRequest(
        pull_request_id=pull_request_id,
        pull_request_name=pull_request_name,
        author_id=author_id,
        status="OPEN"
    )

    # Assign reviewers
    reviewer_ids = assign_reviewers(db, author_id)
    reviewers = db.query(User).filter(User.user_id.in_(reviewer_ids)).all()
    pr.assigned_reviewers = reviewers

    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def merge_pull_request(db: Session, pull_request_id: str) -> PullRequest:
    pr = db.query(PullRequest).filter(
        PullRequest.pull_request_id == pull_request_id
    ).first()
    if not pr:
        raise PRNotFoundError(f"PR '{pull_request_id}' not found")

    # Idempotent: if already merged, just return
    if pr.status == "MERGED":
        return pr

    from datetime import datetime
    pr.status = "MERGED"
    pr.merged_at = datetime.utcnow()
    db.commit()
    db.refresh(pr)
    return pr


def reassign_reviewer(
    db: Session,
    pull_request_id: str,
    old_user_id: str
) -> tuple[PullRequest, str]:
    pr = db.query(PullRequest).filter(
        PullRequest.pull_request_id == pull_request_id
    ).first()
    if not pr:
        raise PRNotFoundError(f"PR '{pull_request_id}' not found")

    # Check if PR is merged
    if pr.status == "MERGED":
        raise PRMergedError("Cannot reassign on merged PR")

    # Check if old_user_id is assigned
    old_reviewer = next((r for r in pr.assigned_reviewers if r.user_id == old_user_id), None)
    if not old_reviewer:
        raise ReviewerNotAssignedError(f"Reviewer '{old_user_id}' is not assigned to this PR")

    # Get candidates from old reviewer's team (excluding old reviewer and author)
    candidates = get_active_reviewers_from_team(
        db,
        old_reviewer.team_name,
        exclude_user_id=old_user_id
    )
    # Also exclude author
    candidates = [c for c in candidates if c.user_id != pr.author_id]
    # Exclude already assigned reviewers
    assigned_ids = [r.user_id for r in pr.assigned_reviewers]
    candidates = [c for c in candidates if c.user_id not in assigned_ids]

    if not candidates:
        raise NoCandidateError("No active replacement candidate in team")

    # Select random candidate
    new_reviewer = random.choice(candidates)

    # Replace reviewer
    pr.assigned_reviewers.remove(old_reviewer)
    pr.assigned_reviewers.append(new_reviewer)

    db.commit()
    db.refresh(pr)
    return pr, new_reviewer.user_id


def get_user_reviews(db: Session, user_id: str) -> List[PullRequest]:
    user = get_user_by_id(db, user_id)
    return user.assigned_prs


def bulk_deactivate_team(db: Session, team_name: str) -> int:
    """Deactivate all users in a team and safely reassign open PRs"""
    team = get_team_by_name(db, team_name)

    # Get all open PRs
    open_prs = db.query(PullRequest).filter(PullRequest.status == "OPEN").all()

    team_user_ids = {user.user_id for user in team.members}

    # Reassign reviewers for open PRs
    reassigned_count = 0
    for pr in open_prs:
        for reviewer in list(pr.assigned_reviewers):
            if reviewer.user_id in team_user_ids:
                try:
                    reassign_reviewer(db, pr.pull_request_id, reviewer.user_id)
                    reassigned_count += 1
                except NoCandidateError:
                    # If no candidate available, leave as is (will be inactive)
                    pass

    # Deactivate all team members
    for user in team.members:
        user.is_active = False

    db.commit()
    return reassigned_count


def get_statistics(db: Session) -> dict:
    """Get service statistics"""
    total_prs = db.query(PullRequest).count()
    open_prs = db.query(PullRequest).filter(PullRequest.status == "OPEN").count()
    merged_prs = db.query(PullRequest).filter(PullRequest.status == "MERGED").count()

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    total_teams = db.query(Team).count()

    # Count reviewer assignments
    reviewer_assignments = {}
    all_prs = db.query(PullRequest).all()
    for pr in all_prs:
        for reviewer in pr.assigned_reviewers:
            reviewer_assignments[reviewer.user_id] = reviewer_assignments.get(reviewer.user_id, 0) + 1

    return {
        "total_prs": total_prs,
        "open_prs": open_prs,
        "merged_prs": merged_prs,
        "total_users": total_users,
        "active_users": active_users,
        "total_teams": total_teams,
        "reviewer_assignments": reviewer_assignments
    }

