import streamlit as st
import pandas as pd
import plotly.express as px


def render_kpi_header(df: pd.DataFrame) -> None:
    """Displays top-level executive summary metrics."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Repositories", df["Repository"].nunique())
    c2.metric("Total Page Views (14d)", f"{int(df['Total Views'].sum()):,}")
    c3.metric("Est. External Visitors (14d)", f"{int(df['Est. Other Visitors'].sum()):,}")
    c4.metric("Total Git Clones (14d)", f"{int(df['Total Clones'].sum()):,}")


def render_traffic_charts(df: pd.DataFrame) -> None:
    """Renders interactive multi-repository Plotly trend charts."""
    tab1, tab2 = st.tabs(["External Visitors Trend", "Git Clones Trend"])

    with tab1:
        fig_visitors = px.line(
            df.sort_values("Date"),
            x="Date",
            y="Est. Other Visitors",
            color="Repository",
            markers=True,
            title="Daily Estimated External Visitors (Excludes Owner)",
            template="plotly_dark",
        )
        fig_visitors.update_layout(hovermode="x unified", yaxis_rangemode="tozero")
        st.plotly_chart(fig_visitors, use_container_width=True)

    with tab2:
        fig_clones = px.bar(
            df.sort_values("Date"),
            x="Date",
            y="Total Clones",
            color="Repository",
            title="Daily Repository Clones (Includes Automated Bots)",
            template="plotly_dark",
        )
        fig_clones.update_layout(hovermode="x unified")
        st.plotly_chart(fig_clones, use_container_width=True)


def render_data_table(df: pd.DataFrame) -> None:
    """Renders a filterable audit log table with CSV export."""
    st.subheader("Daily Repository Audit Log")
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_repos = st.multiselect(
            "Filter Repositories",
            options=sorted(df["Repository"].unique()),
            default=[],
            placeholder="All repositories",
        )
    with col2:
        only_external = st.checkbox("Only show days with external visitors (> 0)", value=False)

    filtered = df.copy()
    if selected_repos:
        filtered = filtered[filtered["Repository"].isin(selected_repos)]
    if only_external:
        filtered = filtered[filtered["Est. Other Visitors"] > 0]

    st.dataframe(filtered, use_container_width=True, hide_index=True)
