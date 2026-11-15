import plotly.express as px
import plotly.graph_objects as go

import pandas as pd

from datapilot.schemas.charts import ChartSpec



def render_chart(spec: ChartSpec) -> go.Figure:
    """Convert a validated chart specification into a Plotly figure."""

    if len(spec.x) != len(spec.y):
        raise ValueError("Chart x and y must have equal lengths.")

    if spec.chart_type == "bar":
        fig = px.bar(
            x=spec.x,
            y=spec.y,
            title=spec.title,
            labels={
                "x": spec.x_label,
                "y": spec.y_label,
            },
        )

    elif spec.chart_type == "line":
        fig = px.line(
            x=spec.x,
            y=spec.y,
            title=spec.title,
            markers=True,
            labels={
                "x": spec.x_label,
                "y": spec.y_label,
            },
        )

    elif spec.chart_type == "pie":
        fig = px.pie(
            names=spec.x,
            values=spec.y,
            title=spec.title,
        )

    else:
        raise ValueError(
            f"Unsupported chart type: {spec.chart_type}"
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=30, t=60, b=40),
    )

    return fig




def build_sales_charts(df: pd.DataFrame) -> list[ChartSpec]:
    """Build deterministic chart specifications from sales data."""

    quarterly = df.copy()
    quarterly["quarter"] = (
        quarterly["month"].dt.to_period("Q").astype(str)
    )

    quarterly = (
        quarterly.groupby("quarter", as_index=False)["revenue"]
        .sum()
        .sort_values("quarter")
    )

    regional = (
        df.groupby("region_name", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )

    category = (
        df.groupby("category", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )

    return [
        ChartSpec(
            chart_id="quarterly_revenue",
            title="Quarterly Revenue Trend",
            chart_type="line",
            x=quarterly["quarter"].tolist(),
            y=quarterly["revenue"].astype(float).tolist(),
            x_label="Quarter",
            y_label="Revenue",
        ),
        ChartSpec(
            chart_id="regional_revenue",
            title="Revenue by Region",
            chart_type="bar",
            x=regional["region_name"].tolist(),
            y=regional["revenue"].astype(float).tolist(),
            x_label="Region",
            y_label="Revenue",
        ),
        ChartSpec(
            chart_id="category_revenue",
            title="Revenue by Product Category",
            chart_type="pie",
            x=category["category"].tolist(),
            y=category["revenue"].astype(float).tolist(),
            x_label="Category",
            y_label="Revenue",
        ),
    ]