import pandas as pd
from typing import List, Dict, Any


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
