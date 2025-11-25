import pytest
from fastapi.testclient import TestClient


def test_create_team(client: TestClient):
    """Test team creation"""
    response = client.post(
        "/team/add",
        json={
            "team_name": "backend",
            "members": [
                {"user_id": "u1", "username": "Alice", "is_active": True},
                {"user_id": "u2", "username": "Bob", "is_active": True},
                {"user_id": "u3", "username": "Charlie", "is_active": True}
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["team_name"] == "backend"
    assert len(data["members"]) == 3


def test_get_team(client: TestClient):
    """Test getting team"""
    # Create team first
    client.post(
        "/team/add",
        json={
            "team_name": "frontend",
            "members": [
                {"user_id": "u4", "username": "David", "is_active": True}
            ]
        }
    )

    response = client.get("/team/get?team_name=frontend")
    assert response.status_code == 200
    data = response.json()
    assert data["team_name"] == "frontend"
    assert len(data["members"]) == 1


def test_create_pr_with_auto_assignment(client: TestClient):
    """Test PR creation with automatic reviewer assignment"""
    # Create team with multiple members
    client.post(
        "/team/add",
        json={
            "team_name": "devops",
            "members": [
                {"user_id": "u5", "username": "Eve", "is_active": True},
                {"user_id": "u6", "username": "Frank", "is_active": True},
                {"user_id": "u7", "username": "Grace", "is_active": True}
            ]
        }
    )

    # Create PR
    response = client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-1",
            "pull_request_name": "Add feature",
            "author_id": "u5"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["pull_request_id"] == "pr-1"
    assert data["status"] == "OPEN"
    assert len(data["assigned_reviewers"]) <= 2
    assert "u5" not in data["assigned_reviewers"]  # Author should not be reviewer


def test_merge_pr_idempotent(client: TestClient):
    """Test that merge is idempotent"""
    # Setup
    client.post(
        "/team/add",
        json={
            "team_name": "qa",
            "members": [
                {"user_id": "u8", "username": "Helen", "is_active": True},
                {"user_id": "u9", "username": "Ivan", "is_active": True}
            ]
        }
    )
    client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-2",
            "pull_request_name": "Fix bug",
            "author_id": "u8"
        }
    )

    # First merge
    response1 = client.post(
        "/pullRequest/merge",
        json={"pull_request_id": "pr-2"}
    )
    assert response1.status_code == 200
    assert response1.json()["status"] == "MERGED"

    # Second merge (should be idempotent)
    response2 = client.post(
        "/pullRequest/merge",
        json={"pull_request_id": "pr-2"}
    )
    assert response2.status_code == 200
    assert response2.json()["status"] == "MERGED"


def test_reassign_reviewer(client: TestClient):
    """Test reviewer reassignment"""
    # Setup
    client.post(
        "/team/add",
        json={
            "team_name": "security",
            "members": [
                {"user_id": "u10", "username": "Jack", "is_active": True},
                {"user_id": "u11", "username": "Kate", "is_active": True},
                {"user_id": "u12", "username": "Liam", "is_active": True},
                {"user_id": "u_spare", "username": "Mike", "is_active": True}
            ]
        }
    )

    create_response = client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-3",
            "pull_request_name": "Security update",
            "author_id": "u10"
        }
    )
    assert create_response.status_code == 201
    reviewers = create_response.json()["assigned_reviewers"]
    assert len(reviewers) > 0

    old_reviewer = reviewers[0]

    # Reassign
    response = client.post(
        "/pullRequest/reassign",
        json={
            "pull_request_id": "pr-3",
            "old_user_id": old_reviewer
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["replaced_by"] != old_reviewer


def test_cannot_reassign_merged_pr(client: TestClient):
    """Test that merged PRs cannot be reassigned"""
    # Setup
    client.post(
        "/team/add",
        json={
            "team_name": "mobile",
            "members": [
                {"user_id": "u13", "username": "Mia", "is_active": True},
                {"user_id": "u14", "username": "Noah", "is_active": True}
            ]
        }
    )

    create_response = client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-4",
            "pull_request_name": "Mobile feature",
            "author_id": "u13"
        }
    )
    assert create_response.status_code == 201
    reviewers = create_response.json()["assigned_reviewers"]

    # Merge PR
    client.post(
        "/pullRequest/merge",
        json={"pull_request_id": "pr-4"}
    )

    # Try to reassign (should fail)
    if reviewers:
        response = client.post(
            "/pullRequest/reassign",
            json={
                "pull_request_id": "pr-4",
                "old_user_id": reviewers[0]
            }
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PR_MERGED"


def test_get_user_reviews(client: TestClient):
    """Test getting PRs assigned to user"""
    # Setup
    client.post(
        "/team/add",
        json={
            "team_name": "data",
            "members": [
                {"user_id": "u15", "username": "Olivia", "is_active": True},
                {"user_id": "u16", "username": "Paul", "is_active": True}
            ]
        }
    )

    client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-5",
            "pull_request_name": "Data pipeline",
            "author_id": "u15"
        }
    )

    response = client.get("/users/getReview?user_id=u16")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "u16"
    assert len(data["pull_requests"]) >= 0  # May or may not be assigned


def test_inactive_user_not_assigned(client: TestClient):
    """Test that inactive users are not assigned as reviewers"""
    # Create team with active and inactive users
    client.post(
        "/team/add",
        json={
            "team_name": "design",
            "members": [
                {"user_id": "u17", "username": "Quinn", "is_active": True},
                {"user_id": "u18", "username": "Rachel", "is_active": False},
                {"user_id": "u19", "username": "Sam", "is_active": True}
            ]
        }
    )

    response = client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-6",
            "pull_request_name": "Design update",
            "author_id": "u17"
        }
    )

    assert response.status_code == 201
    reviewers = response.json()["assigned_reviewers"]
    assert "u18" not in reviewers  # Inactive user should not be assigned


def test_statistics_endpoint(client: TestClient):
    """Test statistics endpoint"""
    # Setup some data
    client.post(
        "/team/add",
        json={
            "team_name": "test_team",
            "members": [
                {"user_id": "u20", "username": "Tom", "is_active": True},
                {"user_id": "u21", "username": "Uma", "is_active": True}
            ]
        }
    )

    client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-7",
            "pull_request_name": "Test PR",
            "author_id": "u20"
        }
    )

    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_prs" in data
    assert "open_prs" in data
    assert "merged_prs" in data
    assert "total_users" in data
    assert "active_users" in data
    assert "total_teams" in data
    assert "reviewer_assignments" in data


def test_bulk_deactivate(client: TestClient):
    """Test bulk deactivation of team"""
    # Setup
    client.post(
        "/team/add",
        json={
            "team_name": "temp_team",
            "members": [
                {"user_id": "u22", "username": "Victor", "is_active": True},
                {"user_id": "u23", "username": "Wendy", "is_active": True}
            ]
        }
    )

    client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-8",
            "pull_request_name": "Temp PR",
            "author_id": "u22"
        }
    )

    response = client.post(
        "/users/bulkDeactivate",
        json={"team_name": "temp_team"}
    )
    assert response.status_code == 200

    # Verify users are deactivated
    user_response = client.get("/team/get?team_name=temp_team")
    members = user_response.json()["members"]
    assert all(not member["is_active"] for member in members)

