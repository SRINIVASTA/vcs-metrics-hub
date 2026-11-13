import streamlit as st
import pandas as pd
from src.config import CACHE_TTL_SECONDS
from src.github_client import GitHubTelemetryClient
from src.analytics import build_telemetry_dataframe, save_and_merge_history
from src.ui_components import (
    render_kpi_header,
    render_traffic_charts,
    render_styled_audit_table,
)

st.set_page_config(
    page_title="GitHub Portfolio Analytics",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Syncing repository telemetry...")
def load_telemetry(token: str):
    client = GitHubTelemetryClient(token)
    username = client.get_authenticated_user()
    repos = client.get_owned_repositories(username)

    raw_records = []
    for repo in repos:
        traffic = client.get_repo_traffic(username, repo["name"])
        raw_records.append(
            {
                "repo": repo["name"],
                "private": repo["private"],
                "traffic": traffic,
            }
        )
    fresh_df = build_telemetry_dataframe(raw_records)
    merged_df = save_and_merge_history(fresh_df)
    return username, merged_df


def render_sidebar_controls(df: pd.DataFrame, username: str) -> pd.DataFrame:
    """Renders all global filters and actions inside the left sidebar."""
    with st.sidebar:
        st.header("⚙️ Telemetry Controls")
        st.caption(f"Connected Account: **`{username}`**")

        if st.button("🔄 Sync Live Data", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        st.subheader("📅 Date Range")
        temp_df = df.copy()
        temp_df["Date_dt"] = pd.to_datetime(temp_df["Date"]).dt.date
        min_date, max_date = temp_df["Date_dt"].min(), temp_df["Date_dt"].max()

        selected_range = st.date_input(
            "Select Start & End Date",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        st.caption(f"Archive spans `{min_date}` to `{max_date}`")

        st.divider()

        st.subheader("🔍 Repository Filters")
        visibility_filter = st.radio(
            "Visibility",
            options=["All", "Public", "Private"],
            horizontal=True,
        )

        selected_repos = st.multiselect(
            "Specific Repositories",
            options=sorted(df["Repository"].unique()),
            default=[],
            placeholder="All repositories",
        )

        only_external = st.toggle(
            "Only External Visitors (> 0)",
            value=False,
            help="ON: Only External Visitors (> 0) | OFF: Only Active Internal Visits (> 0)",
        )

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start_d, end_d = selected_range
            temp_df = temp_df[(temp_df["Date_dt"] >= start_d) & (temp_df["Date_dt"] <= end_d)]

        if visibility_filter != "All":
            temp_df = temp_df[temp_df["Visibility"] == visibility_filter]

        if selected_repos:
            temp_df = temp_df[temp_df["Repository"].isin(selected_repos)]

        if only_external:
            temp_df = temp_df[temp_df["Est. Other Visitors"] > 0]
        else:
            # Show only active repositories with internal (owner-only) views
            temp_df = temp_df[
                (temp_df["Total Views"] > 0) & (temp_df["Est. Other Visitors"] == 0)
            ]

        st.divider()
        st.caption("GitHub Portfolio Analytics • Telemetry")

    return temp_df.drop(columns=["Date_dt"]).reset_index(drop=True)


def main():
    st.title("📊 GitHub Portfolio Analytics")
    st.caption("Cross-Repository Traffic, External Visitor & Clone Telemetry")

    if "GITHUB_TOKEN" not in st.secrets:
        st.error("Missing `GITHUB_TOKEN` in `.streamlit/secrets.toml`.")
        st.stop()

    try:
        username, df = load_telemetry(st.secrets["GITHUB_TOKEN"])
    except Exception as exc:
        st.error(f"Failed to fetch telemetry from GitHub API: {exc}")
        st.stop()

    if df.empty:
        st.info(f"No traffic or clone events recorded for `{username}` yet.")
        return

    filtered_df = render_sidebar_controls(df, username)

    if filtered_df.empty:
        st.warning("No telemetry records match your current sidebar filters.")
        return

    render_kpi_header(filtered_df)
    st.divider()
    render_traffic_charts(filtered_df)
    st.divider()
    render_styled_audit_table(filtered_df)


if __name__ == "__main__":
    main()
