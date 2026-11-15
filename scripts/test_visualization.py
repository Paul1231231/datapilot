from pathlib import Path

from datapilot.analytics.sales import load_sales_data
from datapilot.visualization.charts import (
    build_sales_charts,
    render_chart,
)


def main():
    output_dir = Path("artifacts/charts")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_sales_data()
    chart_specs = build_sales_charts(df)

    for spec in chart_specs:
        figure = render_chart(spec)

        output_path = output_dir / f"{spec.chart_id}.html"

        figure.write_html(str(output_path))

        print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()