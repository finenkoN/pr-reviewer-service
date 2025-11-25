from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Association table for many-to-many relationship between PRs and reviewers
pr_reviewers = Table(
    'pr_reviewers',
    Base.metadata,
    Column('pull_request_id', String, ForeignKey('pull_requests.pull_request_id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.user_id'), primary_key=True)
)


class Team(Base):
    __tablename__ = "teams"

    team_name = Column(String, primary_key=True)
    members = relationship("User", back_populates="team", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    team_name = Column(String, ForeignKey("teams.team_name"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    team = relationship("Team", back_populates="members")
    assigned_prs = relationship(
        "PullRequest",
        secondary=pr_reviewers,
        back_populates="assigned_reviewers"
    )


class PullRequest(Base):
    __tablename__ = "pull_requests"

    pull_request_id = Column(String, primary_key=True)
    pull_request_name = Column(String, nullable=False)
    author_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(String, nullable=False, default="OPEN")  # OPEN or MERGED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    merged_at = Column(DateTime(timezone=True), nullable=True)

    author = relationship("User", foreign_keys=[author_id])
    assigned_reviewers = relationship(
        "User",
        secondary=pr_reviewers,
        back_populates="assigned_prs"
    )

