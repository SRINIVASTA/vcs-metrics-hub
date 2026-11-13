import requests
from typing import Dict, List, Any
from src.config import API_BASE_URL, REQUEST_TIMEOUT


class GitHubTelemetryClient:
    """Enterprise client for fetching repository traffic metrics."""

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_authenticated_user(self) -> str:
        """Dynamically resolves the token owner's username."""
        resp = requests.get(
            f"{API_BASE_URL}/user", headers=self.headers, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()["login"]

    def get_owned_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Fetches all public and private repositories owned by the user."""
        repos = []
        page = 1
        while True:
            resp = requests.get(
                f"{API_BASE_URL}/user/repos",
                headers=self.headers,
                params={"per_page": 100, "page": page, "affiliation": "owner"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            repos.extend(
                [r for r in batch if r["owner"]["login"].lower() == username.lower()]
            )
            page += 1
        return repos

    def get_repo_traffic(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Retrieves 14-day views and clones for a single repository."""
        views_resp = requests.get(
            f"{API_BASE_URL}/repos/{username}/{repo_name}/traffic/views",
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        clones_resp = requests.get(
            f"{API_BASE_URL}/repos/{username}/{repo_name}/traffic/clones",
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        return {
            "views": views_resp.json().get("views", []) if views_resp.ok else [],
            "clones": clones_resp.json().get("clones", []) if clones_resp.ok else [],
        }
