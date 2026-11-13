import streamlit as st
import pandas as pd
import plotly.express as px


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


def _style_visibility(val: str) -> str:
    """Colors Public and Private status cells cleanly."""
    if val == "Public":
        return "background-color: rgba(46, 160, 67, 0.25); color: #3FB950; font-weight: 600;"
    return "background-color: rgba(210, 153, 34, 0.25); color: #D29922; font-weight: 600;"


def _highlight_external(val: int) -> str:
    """Highlights days where outside visitors viewed the repository."""
    if val >= 5:
        return "background-color: rgba(46, 160, 67, 0.48); color: #FFFFFF; font-weight: 700;"
    if val > 0:
        return "background-color: rgba(46, 160, 67, 0.22); color: #7EE787; font-weight: 600;"
    return "color: #8B949E;"


def _style_views(val: int) -> str:
    """Applies blue intensity tiers without needing matplotlib."""
    if val >= 100:
        return "background-color: rgba(47, 129, 247, 0.45); color: #FFFFFF; font-weight: 700;"
    if val >= 10:
        return "background-color: rgba(47, 129, 247, 0.25); color: #79C0FF; font-weight: 600;"
    if val > 0:
        return "background-color: rgba(47, 129, 247, 0.10); color: #A5D6FF;"
    return "color: #8B949E;"


def _style_clones(val: int) -> str:
    """Applies purple intensity tiers without needing matplotlib."""
    if val >= 100:
        return "background-color: rgba(163, 113, 247, 0.45); color: #FFFFFF; font-weight: 700;"
    if val >= 10:
        return "background-color: rgba(163, 113, 247, 0.25); color: #D2A8FF; font-weight: 600;"
    if val > 0:
        return "background-color: rgba(163, 113, 247, 0.10); color: #E2C5FF;"
    return "color: #8B949E;"


def render_styled_audit_table(df: pd.DataFrame) -> None:
    """Renders a color-graded enterprise audit log table with weekday names."""
    st.subheader("Daily Repository Audit Log")

    display_df = df.copy()
    day_names = pd.to_datetime(display_df["Date"]).dt.day_name()
    display_df.insert(1, "Day", day_names)

    num_cols = [
        "Total Views",
        "Unique Visitors",
        "Est. Other Visitors",
        "Total Clones",
        "Unique Cloners",
    ]
    for col in num_cols:
        if col in display_df.columns:
            display_df[col] = pd.to_numeric(display_df[col], errors="coerce").fillna(0).astype(int)

    # Streamlit's browser grid throws "Error during cell creation" above ~1,000 styled rows.
    # Apply rich cell styling for <= 800 rows; use fast native rendering for larger datasets.
    if len(display_df) <= 800:
        styled_df = (
            display_df.style
            .map(_style_visibility, subset=["Visibility"])
            .map(_highlight_external, subset=["Est. Other Visitors"])
            .map(_style_views, subset=["Total Views"])
            .map(_style_clones, subset=["Total Clones"])
            .format({col: "{:,}" for col in num_cols if col in display_df.columns})
        )
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.caption(
            f"Showing {len(display_df):,} records (cell color highlights auto-enable when filtered to ≤ 800 rows)."
        )
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                col: st.column_config.NumberColumn(format="%d")
                for col in num_cols
                if col in display_df.columns
            },
        )
