import streamlit as st
import pandas as pd
import plotly.express as px


def render_date_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Renders a custom start/end date picker across all available history."""
    temp_df = df.copy()
    temp_df["Date_dt"] = pd.to_datetime(temp_df["Date"]).dt.date
    min_date, max_date = temp_df["Date_dt"].min(), temp_df["Date_dt"].max()

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    with col2:
        st.caption(f"Available history: **{min_date}** to **{max_date}**")

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_d, end_d = selected_range
        temp_df = temp_df[(temp_df["Date_dt"] >= start_d) & (temp_df["Date_dt"] <= end_d)]

    return temp_df.drop(columns=["Date_dt"]).reset_index(drop=True)


def render_kpi_header(df: pd.DataFrame) -> None:
    """Displays top-level executive summary metrics for the selected dates."""
    days_count = df["Date"].nunique() if not df.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Repositories", df["Repository"].nunique())
    c2.metric(f"Total Page Views ({days_count}d)", f"{int(df['Total Views'].sum()):,}")
    c3.metric(f"Est. External Visitors ({days_count}d)", f"{int(df['Est. Other Visitors'].sum()):,}")
    c4.metric(f"Total Git Clones ({days_count}d)", f"{int(df['Total Clones'].sum()):,}")


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
    col1, col2 = st.columns(2)

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
