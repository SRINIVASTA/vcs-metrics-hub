import os
from src.github_client import fetch_all_repo_traffic
from src.analytics import build_telemetry_dataframe, save_and_merge_history


def main():
    token = os.environ.get("GH_PAT")
    if not token:
        raise ValueError("Missing GH_PAT environment variable.")

    raw_records = fetch_all_repo_traffic(token)
    new_df = build_telemetry_dataframe(raw_records)
    save_and_merge_history(new_df)
    print("Successfully synced completed traffic history up to yesterday UTC.")


if __name__ == "__main__":
    main()
