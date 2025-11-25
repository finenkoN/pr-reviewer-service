"""
Load testing script for Locust
Run with: locust -f tests/load_test.py --host=http://localhost:8080
"""
from locust import HttpUser, task, between
import random
import string


def generate_id(prefix="", length=5):
    """Generate random ID"""
    chars = string.ascii_lowercase + string.digits
    return f"{prefix}{''.join(random.choices(chars, k=length))}"


class PRReviewerUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Wait between 0.1 and 0.5 seconds between tasks

    def on_start(self):
        """Setup: create a team and users"""
        self.team_name = generate_id("team_")
        self.user_ids = [generate_id("u") for _ in range(5)]

        members = [
            {"user_id": uid, "username": f"User_{uid}", "is_active": True}
            for uid in self.user_ids
        ]

        self.client.post(
            "/team/add",
            json={"team_name": self.team_name, "members": members}
        )

    @task(3)
    def create_pr(self):
        """Create a PR (most common operation)"""
        author_id = random.choice(self.user_ids)
        pr_id = generate_id("pr_")

        self.client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": pr_id,
                "pull_request_name": f"PR {pr_id}",
                "author_id": author_id
            }
        )

    @task(2)
    def get_team(self):
        """Get team info"""
        self.client.get(f"/team/get?team_name={self.team_name}")

    @task(1)
    def get_user_reviews(self):
        """Get user reviews"""
        user_id = random.choice(self.user_ids)
        self.client.get(f"/users/getReview?user_id={user_id}")

    @task(1)
    def get_stats(self):
        """Get statistics"""
        self.client.get("/stats")

    @task(1)
    def merge_pr(self):
        """Merge a PR (less frequent)"""
        # In real scenario, we'd track created PRs, but for load test we'll use random IDs
        pr_id = generate_id("pr_")
        self.client.post(
            "/pullRequest/merge",
            json={"pull_request_id": pr_id}
        )

