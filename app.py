import streamlit as st
from src.config import CACHE_TTL_SECONDS
from src.github_client import GitHubTelemetryClient
from src.analytics import build_telemetry_dataframe
from src.ui_components import render_kpi_header, render_traffic_charts, render_data_table

st.set_page_config(page_title="VCS Metrics Hub", page_icon="📊", layout="wide")


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
    return username, build_telemetry_dataframe(raw_records)


def main():
    st.title("📊 VCS Metrics Hub")
    st.caption("14-Day Cross-Repository Traffic & Clone Telemetry")

    if "GITHUB_TOKEN" not in st.secrets:
        st.error("Missing `GITHUB_TOKEN` in `.streamlit/secrets.toml`.")
        st.stop()

    try:
        username, df = load_telemetry(st.secrets["GITHUB_TOKEN"])
    except Exception as exc:
        st.error(f"Failed to fetch telemetry from GitHub API: {exc}")
        st.stop()

    if df.empty:
        st.info(f"No traffic or clone events recorded for `{username}` in the last 14 days.")
        return

    render_kpi_header(df)
    st.divider()
    render_traffic_charts(df)
    st.divider()
    render_data_table(df)


if __name__ == "__main__":
    main()
