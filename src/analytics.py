import os
from datetime import datetime, timezone
import pandas as pd
from typing import List, Dict, Any

HISTORY_FILE = "data/traffic_history.csv"


def build_telemetry_dataframe(raw_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Transforms raw API payloads into a structured daily analytics table."""
    rows = []

    for item in raw_records:
        repo_name = item["repo"]
        visibility = "Private" if item["private"] else "Public"
        clones_map = {
            c["timestamp"][:10]: (c["count"], c["uniques"])
            for c in item["traffic"]["clones"]
        }
        views_map = {
            v["timestamp"][:10]: (v["count"], v["uniques"])
            for v in item["traffic"]["views"]
        }

        all_dates = sorted(set(views_map.keys()) | set(clones_map.keys()))

        for date in all_dates:
            total_views, unique_visitors = views_map.get(date, (0, 0))
            total_clones, unique_cloners = clones_map.get(date, (0, 0))
            est_external_visitors = max(0, unique_visitors - 1)

            rows.append(
                {
                    "Date": date,
                    "Repository": repo_name,
                    "Visibility": visibility,
                    "Total Views": total_views,
                    "Unique Visitors": unique_visitors,
                    "Est. Other Visitors": est_external_visitors,
                    "Total Clones": total_clones,
                    "Unique Cloners": unique_cloners,
                }
            )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["Date", "Repository"], ascending=[False, True]).reset_index(drop=True)
    return df


def save_and_merge_history(new_df: pd.DataFrame) -> pd.DataFrame:
    """Archives completed days (up to yesterday UTC) to CSV and keeps today's data live in memory."""
    os.makedirs("data", exist_ok=True)
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if not new_df.empty:
        completed_new_df = new_df[new_df["Date"] < today_utc].copy()
        today_live_df = new_df[new_df["Date"] >= today_utc].copy()
    else:
        completed_new_df = pd.DataFrame()
        today_live_df = pd.DataFrame()

    if os.path.exists(HISTORY_FILE):
        old_df = pd.read_csv(HISTORY_FILE)
        old_df = old_df[old_df["Date"] < today_utc]
        if not completed_new_df.empty:
            archived_df = pd.concat([old_df, completed_new_df], ignore_index=True)
            archived_df = archived_df.drop_duplicates(subset=["Date", "Repository"], keep="last")
        else:
            archived_df = old_df
    else:
        archived_df = completed_new_df.copy()

    if not archived_df.empty:
        archived_df = archived_df.sort_values(by=["Date", "Repository"], ascending=[False, True]).reset_index(drop=True)
        archived_df.to_csv(HISTORY_FILE, index=False)

    dashboard_df = pd.concat([archived_df, today_live_df], ignore_index=True)
    if not dashboard_df.empty:
        dashboard_df = dashboard_df.sort_values(by=["Date", "Repository"], ascending=[False, True]).reset_index(drop=True)

    return dashboard_df
