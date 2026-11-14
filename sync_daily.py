import os
from src.github_client import GitHubTelemetryClient
from src.analytics import build_telemetry_dataframe, save_and_merge_history


def main():
    token = os.environ.get("GH_PAT")
    if not token:
        raise ValueError("Missing GH_PAT environment variable.")

    client = GitHubTelemetryClient(token)
    username = client.get_authenticated_user()
    repos = client.get_owned_repositories(username)

    raw_records = []
    for repo in repos:
        repo_name = repo["name"]
        traffic = client.get_repo_traffic(username, repo_name)
        raw_records.append(
            {
                "repo": repo_name,
                "private": repo.get("private", False),
                "traffic": traffic,
            }
        )

    new_df = build_telemetry_dataframe(raw_records)
    save_and_merge_history(new_df)
    print(f"Successfully synced {len(repos)} repositories up to yesterday UTC for @{username}.")


if __name__ == "__main__":
    main()
