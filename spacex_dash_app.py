"""Interactive Plotly Dash dashboard for the SpaceX launch dataset."""

from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html


ROOT = Path(__file__).resolve().parent
spacex_df = pd.read_csv(ROOT / "data" / "spacex_launch_dash.csv")
site_options = [{"label": "All Sites", "value": "ALL"}]
site_options.extend(
    {"label": site, "value": site}
    for site in sorted(spacex_df["Launch Site"].dropna().unique())
)

min_payload = int(spacex_df["Payload Mass (kg)"].min())
max_payload = int(spacex_df["Payload Mass (kg)"].max())

app = Dash(__name__)
app.title = "SpaceX Landing Dashboard"
app.layout = html.Div(
    [
        html.H1("SpaceX Falcon 9 Landing Dashboard", style={"textAlign": "center"}),
        html.Label("Select a launch site:"),
        dcc.Dropdown(
            id="site-dropdown",
            options=site_options,
            value="ALL",
            placeholder="Select a Launch Site here",
            searchable=True,
        ),
        dcc.Graph(id="success-pie-chart"),
        html.Label("Select payload range (kg):"),
        dcc.RangeSlider(
            id="payload-slider",
            min=0,
            max=10000,
            step=1000,
            marks={0: "0", 2500: "2.5k", 5000: "5k", 7500: "7.5k", 10000: "10k"},
            value=[min_payload, max_payload],
        ),
        dcc.Graph(id="success-payload-scatter-chart"),
    ],
    style={"maxWidth": "1100px", "margin": "0 auto", "padding": "24px"},
)


@app.callback(
    Output("success-pie-chart", "figure"),
    Input("site-dropdown", "value"),
)
def get_pie_chart(entered_site: str):
    filtered_df = spacex_df if entered_site == "ALL" else spacex_df[spacex_df["Launch Site"] == entered_site]
    title = "Landing outcomes across all launch sites" if entered_site == "ALL" else f"Landing outcomes at {entered_site}"
    fig = px.pie(filtered_df, names="class", hole=0.42, title=title)
    fig.update_traces(
        textinfo="label+percent",
        labels=["Failure", "Success"],
        marker={"colors": ["#D1495B", "#2A9D8F"]},
    )
    return fig


@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    [
        Input("site-dropdown", "value"),
        Input("payload-slider", "value"),
    ],
)
def get_scatter_chart(entered_site: str, payload_range: list[int]):
    filtered_df = spacex_df[
        spacex_df["Payload Mass (kg)"].between(payload_range[0], payload_range[1])
    ]
    if entered_site != "ALL":
        filtered_df = filtered_df[filtered_df["Launch Site"] == entered_site]
    title = "Landing outcome by payload and booster"
    if entered_site != "ALL":
        title += f" - {entered_site}"
    fig = px.scatter(
        filtered_df,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        hover_data=["Flight Number", "Launch Site", "Booster Version"],
        title=title,
    )
    fig.update_yaxes(tickmode="array", tickvals=[0, 1], ticktext=["Failure", "Success"])
    return fig


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

