import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import sqlite3

# Load data
conn = sqlite3.connect("lab_inventory.db")
df = pd.read_sql("SELECT * FROM experiment_logs", conn)
conn.close()
# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Lab Management Dashboard"

# Sidebar layout
sidebar = dbc.Col([
    html.H2("Lab Dashboard", className="text-white mt-4 mb-4 text-center"),
    html.Hr(),
    html.P("Filters", className="text-white text-center"),
    html.Label("Researcher", className="text-white"),
    dcc.Dropdown(
        id='researcher-filter',
        options=[{'label': r, 'value': r} for r in sorted(df['researcher'].unique())],
        multi=True,
        style={"color": "#000"}
    ),
    html.Label("Chemical", className="text-white mt-3"),
    dcc.Dropdown(
        id='chemical-filter',
        options=[{'label': c, 'value': c} for c in sorted(df['chemical'].unique())],
        multi=True,
        style={"color": "#000"}
    ),
    html.Label("Instrument", className="text-white mt-3"),
    dcc.Dropdown(
        id='instrument-filter',
        options=[{'label': i, 'value': i} for i in sorted(df['instrument_used'].unique())],
        multi=True,
        style={"color": "#000"}
    ),
    html.Div("\u00a0" * 10)
], width=3, className="bg-dark p-4")

# Main content layout
content = dbc.Col([
    dbc.Row([
        dbc.Col(html.Div(id='total-cost', className="text-light text-center mb-4"), md=4),
        dbc.Col(html.Div(id='unique-instruments', className="text-light text-center mb-4"), md=4),
        dbc.Col(html.Div(id='busiest-day', className="text-light text-center mb-4"), md=4)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='chemical-usage-bubble'), md=6),
        dbc.Col(dcc.Graph(id='cost-distribution-sunburst'), md=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='instrument-usage-polar'), md=6),
        dbc.Col(dcc.Graph(id='daily-cost-line'), md=6)
    ])
], width=9)

app.layout = dbc.Container([
    dbc.Row([
        sidebar,
        content
    ])
], fluid=True)

# Callbacks for graphs and KPIs
@app.callback(
    [Output('chemical-usage-bubble', 'figure'),
     Output('cost-distribution-sunburst', 'figure'),
     Output('instrument-usage-polar', 'figure'),
     Output('daily-cost-line', 'figure'),
     Output('total-cost', 'children'),
     Output('unique-instruments', 'children'),
     Output('busiest-day', 'children')],
    [Input('researcher-filter', 'value'),
     Input('chemical-filter', 'value'),
     Input('instrument-filter', 'value')]
)
def update_dashboard(researchers, chemicals, instruments):
    dff = df.copy()
    if researchers:
        dff = dff[dff['researcher'].isin(researchers)]
    if chemicals:
        dff = dff[dff['chemical'].isin(chemicals)]
    if instruments:
        dff = dff[dff['instrument_used'].isin(instruments)]

    # Bubble chart: Quantity vs Total Cost by Chemical
    bubble_fig = px.scatter(
        dff,
        x='quantity_used_ml', y='total_cost',
        size='total_cost', color='chemical',
        hover_name='chemical',
        title="Chemical Cost vs Quantity",
        template="plotly_dark"
    )

    # Sunburst chart: Instrument -> Chemical -> Researcher
    sunburst_fig = px.sunburst(
        dff,
        path=['instrument_used', 'chemical', 'researcher'],
        values='total_cost',
        title="Cost Breakdown by Instrument, Chemical, and Researcher",
        template="plotly_dark"
    )

    # Polar chart: Avg cost per instrument
    polar_df = dff.groupby('instrument_used')['total_cost'].mean().reset_index()
    polar_fig = px.line_polar(
        polar_df,
        r='total_cost', theta='instrument_used',
        line_close=True,
        title="Average Cost per Instrument",
        template="plotly_dark"
    )

    # Line chart: Daily total cost
    daily_cost = px.line(
        dff.groupby('date')['total_cost'].sum().reset_index(),
        x='date', y='total_cost',
        title="Daily Total Cost", template="plotly_dark"
    )

    total_cost_val = f"Total Cost: ₹{dff['total_cost'].sum():,.2f}"
    unique_instr_val = f"Instruments Used: {dff['instrument_used'].nunique()}"
    busiest_day_val = dff['date'].value_counts().idxmax()
    busiest_day = f"Busiest Day: {busiest_day_val}"

    return bubble_fig, sunburst_fig, polar_fig, daily_cost, total_cost_val, unique_instr_val, busiest_day

if __name__ == '__main__':
    app.run(debug=True)
