"""
DC House Dashboard - Plotly Dash App
Interactive web-based dashboard for DC House Nanogrid monitoring
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import our custom modules
from queries import InfluxDBHelper
from visualizations_plotly import (
    plot_timeseries, plot_multi_timeseries, plot_bar_chart,
    plot_gauge, plot_stat, plot_bar_gauge, plot_pie_chart
)
from energy_savings import EnergyCalculator, simulate_outdoor_temperature


# ============================================================================
# CONFIGURATION
# ============================================================================

INFLUX_CONFIG = {
    'url': 'http://159.203.70.114:8086',
    'token': 'ppl7TgaEtWrzrnO3PzNl3IResAeisDrU32bHsVXPHNZeMmGM7-s-N5U98NrYoArkdEOIHa6R8qKOy_4SyJO46g==',
    'org': 'dchouse'
}

# Dashboard time ranges
TIME_RANGES = {
    'default': '-24h',
    'energy_bill': '-30d',
    'mpc_savings': '-30d',
}


# ============================================================================
# INITIALIZE CONNECTIONS
# ============================================================================

# Initialize database and energy calculator
db = InfluxDBHelper(**INFLUX_CONFIG)
energy_calc = EnergyCalculator()


# ============================================================================
# INITIALIZE DASH APP
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
    ],
    suppress_callback_exceptions=True
)
app.title = "DC House Nanogrid Dashboard"


# ============================================================================
# HELPER FUNCTIONS FOR LAYOUT
# ============================================================================

def create_time_range_options():
    """Create time range options for dropdowns."""
    return [
        {'label': 'Last 24 Hours', 'value': '-24h'},
        {'label': 'Last 3 Days', 'value': '-3d'},
        {'label': 'Last 7 Days', 'value': '-7d'},
        {'label': 'Last 14 Days', 'value': '-14d'},
        {'label': 'Last 30 Days', 'value': '-30d'},
        {'label': 'Last 90 Days', 'value': '-90d'}
    ]


def create_collapsible_row(row_id, title, content, default_time_range='-7d'):
    """
    Create a collapsible row with a time range selector.

    Parameters:
    -----------
    row_id : str
        Unique identifier for the row
    title : str
        Title of the section
    content : list
        List of Dash components to include in the row
    default_time_range : str
        Default time range for this section

    Returns:
    --------
    dbc.Card component with collapsible content
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-chevron-down", id=f"{row_id}-icon"), f"  {title}"],
                        id=f"{row_id}-toggle",
                        color="link",
                        style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#34495e', 'textDecoration': 'none'}
                    ),
                ], style={'flex': '1'}),
                html.Div([
                    html.Label("Time Range:", style={'marginRight': '10px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id=f"{row_id}-time-range",
                        options=create_time_range_options(),
                        value=default_time_range,
                        style={'width': '200px'},
                        clearable=False
                    )
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'})
        ]),
        dbc.Collapse(
            dbc.CardBody(content),
            id=f"{row_id}-collapse",
            is_open=True
        )
    ], style={'marginBottom': '20px'})


# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

app.layout = html.Div([
    # Header
    html.H1(
        "DC House Nanogrid Dashboard",
        style={
            'textAlign': 'center',
            'color': '#2c3e50',
            'marginBottom': '20px',
            'marginTop': '20px',
            'fontWeight': 'bold'
        }
    ),

    # Row 1: High Level Overview
    create_collapsible_row(
        row_id='overview',
        title='High Level Overview',
        content=[
            html.Div([
                html.Div([dcc.Graph(id='indoor-temp-graph')], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='energy-bill-gauge')], style={'width': '25%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='device-usage-pie')], style={'width': '25%', 'display': 'inline-block'}),
            ], style={'display': 'flex'})
        ],
        default_time_range='-24h'
    ),

    # Row 2: Energy Usage
    create_collapsible_row(
        row_id='energy',
        title='Energy Usage',
        content=[dcc.Graph(id='energy-usage-graph')],
        default_time_range='-24h'
    ),

    # Row 3: Heat Pumps
    create_collapsible_row(
        row_id='heat-pumps',
        title='Heat Pumps',
        content=[
            html.Div([
                html.Div([dcc.Graph(id='hp-temp-graph')], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='hp-power-graph')], style={'width': '50%', 'display': 'inline-block'}),
            ], style={'display': 'flex'})
        ],
        default_time_range='-24h'
    ),

    # Row 4: Heat Pump Water Heater
    create_collapsible_row(
        row_id='water-heater',
        title='Heat Pump Water Heater',
        content=[
            html.Div([
                html.Div([dcc.Graph(id='hpwh-temp-graph')], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='hpwh-power-graph')], style={'width': '50%', 'display': 'inline-block'}),
            ], style={'display': 'flex'})
        ],
        default_time_range='-24h'
    ),

    # Row 5: Indoor Environment
    create_collapsible_row(
        row_id='indoor',
        title='Indoor Environment',
        content=[
            html.Div([
                html.Div([dcc.Graph(id='indoor-temp-timeseries')], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='indoor-humidity-timeseries')], style={'width': '50%', 'display': 'inline-block'}),
            ], style={'display': 'flex'})
        ],
        default_time_range='-24h'
    ),

    # Row 6: Energy Consumption
    create_collapsible_row(
        row_id='energy-consumption',
        title='Energy Consumption Analysis',
        content=[dcc.Graph(id='energy-consumption-graph')],
        default_time_range='-24h'
    ),

    # Row 7: Energy Metrics
    create_collapsible_row(
        row_id='energy-metrics',
        title='Energy & Cost Metrics',
        content=[
            html.Div([
                html.Div([dcc.Graph(id='total-energy-stat')], style={'width': '25%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='total-cost-gauge')], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id='co2-emissions-stat')], style={'width': '25%', 'display': 'inline-block'}),
            ], style={'display': 'flex'})
        ],
        default_time_range='-24h'
    ),

    # Refresh interval
    dcc.Interval(
        id='interval-component',
        interval=30*60*1000,  # 30 minutes in milliseconds
        n_intervals=0
    )
], style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh', 'padding': '20px'})


# ============================================================================
# COLLAPSE CALLBACKS - TOGGLE ROW VISIBILITY
# ============================================================================

# Create collapse callbacks for each section
sections = ['overview', 'energy', 'heat-pumps', 'water-heater', 'indoor', 'energy-consumption', 'energy-metrics']

for section in sections:
    @app.callback(
        [Output(f"{section}-collapse", "is_open"),
         Output(f"{section}-icon", "className")],
        [Input(f"{section}-toggle", "n_clicks")],
        [State(f"{section}-collapse", "is_open")],
    )
    def toggle_collapse(n_clicks, is_open, section=section):
        """Toggle collapse state and update icon."""
        if n_clicks:
            is_open = not is_open
        icon_class = "fas fa-chevron-down" if is_open else "fas fa-chevron-right"
        return is_open, icon_class


# ============================================================================
# CALLBACK FUNCTIONS - DATA FETCHING AND PLOTTING
# ============================================================================

@app.callback(
    Output('indoor-temp-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('overview-time-range', 'value')
)
def update_indoor_temp(n, time_range):
    """Plot indoor temperature time series."""
    try:
        indoor_df = db.get_indoor_temperature(start_time=time_range)

        if indoor_df.empty:
            return create_error_figure("No indoor temperature data available")

        return plot_timeseries(
            indoor_df,
            time_col='_time',
            value_col='_value',
            title='Indoor Temperature',
            ylabel='Temperature',
            unit='celsius',
            color='#FF6B6B'
        )
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('energy-bill-gauge', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('overview-time-range', 'value')
)
def update_energy_bill(n, time_range):
    """Plot predicted energy bill gauge."""
    try:
        bill_df = db.get_predicted_energy_bill(start_time=time_range)

        if not bill_df.empty and 'value' in bill_df.columns:
            bill_value = bill_df['value'].iloc[0]
        else:
            # Estimate based on grid power
            power_df = db.get_grid_power(start_time=time_range)
            if not power_df.empty:
                total_kwh = power_df['_value'].sum() / 1000
                bill_value = total_kwh * 0.15
            else:
                bill_value = 0

        return plot_gauge(
            bill_value,
            title='Predicted Energy Bill',
            unit='currencyUSD',
            min_val=0,
            max_val=300,
            thresholds=[0, 100, 200, 300],
            threshold_colors=['#73BF69', '#F2CC0C', '#FF9933', '#E02F44']
        )
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('device-usage-pie', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('overview-time-range', 'value')
)
def update_device_usage(n, time_range):
    """Plot device energy usage pie chart."""
    try:
        device_df = db.get_energy_usage_by_device(start_time=time_range)

        if not device_df.empty and '_measurement' in device_df.columns:
            # Group by device and sum
            device_totals = device_df.groupby('_measurement')['_value'].sum()
            # Get top 5 devices
            top_devices = device_totals.nlargest(5)

            # Convert from Wh to kWh
            top_devices_kwh = top_devices / 1000

            return plot_pie_chart(
                list(top_devices_kwh.index),
                list(top_devices_kwh.values),
                title='Device Energy Usage',
                unit='kwatth',
                show_percentages=True
            )
        else:
            # Show sample data if no real data
            labels = ['HVAC', 'Water Heater', 'Appliances', 'Lighting', 'Other']
            values = [45, 20, 15, 10, 10]
            return plot_pie_chart(
                labels,
                values,
                title='Device Energy Usage',
                unit='percent',
                show_percentages=True
            )
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('energy-usage-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('energy-time-range', 'value')
)
def update_energy_usage(n, time_range):
    """Plot energy usage over time."""
    try:
        power_df = db.get_grid_power(start_time=time_range)

        if not power_df.empty:
            # Convert power to energy (kWh)
            power_df['_value'] = power_df['_value'] / 1000  # Convert to kW

            return plot_timeseries(
                power_df,
                time_col='_time',
                value_col='_value',
                title='Energy Usage Over Time',
                ylabel='Power',
                unit='kwatth',
                color='#4ECDC4'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('hp-temp-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('heat-pumps-time-range', 'value')
)
def update_hp_temp(n, time_range):
    """Plot heat pump temperature time series."""
    try:
        hp_temp_df = db.get_heat_pump_temperature(start_time=time_range)

        if not hp_temp_df.empty:
            return plot_timeseries(
                hp_temp_df,
                time_col='_time',
                value_col='_value',
                title='Heat Pump Temperature Time Series',
                ylabel='Temperature',
                unit='celsius',
                color='#FF6B6B'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('hp-power-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('heat-pumps-time-range', 'value')
)
def update_hp_power(n, time_range):
    """Plot heat pump power consumption."""
    try:
        hp_power_df = db.get_heat_pump_power(start_time=time_range)

        if not hp_power_df.empty:
            return plot_timeseries(
                hp_power_df,
                time_col='_time',
                value_col='_value',
                title='Air Source Heat Pump Power Consumption',
                ylabel='Power',
                unit='watts',
                color='#95E1D3'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('hpwh-temp-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('water-heater-time-range', 'value')
)
def update_hpwh_temp(n, time_range):
    """Plot heat pump water heater temperature time series."""
    try:
        hpwh_temp_df = db.get_hp_water_heater_temperature(start_time=time_range)

        if not hpwh_temp_df.empty:
            return plot_timeseries(
                hpwh_temp_df,
                time_col='_time',
                value_col='_value',
                title='Heat Pump Water Heater Temperature Time Series',
                ylabel='Temperature',
                unit='celsius',
                color='#FFB6B9',
                yaxis_range=[0, 60]
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('hpwh-power-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('water-heater-time-range', 'value')
)
def update_hpwh_power(n, time_range):
    """Plot heat pump water heater power consumption."""
    try:
        hpwh_power_df = db.get_hp_water_heater_power(start_time=time_range)

        if not hpwh_power_df.empty:
            return plot_timeseries(
                hpwh_power_df,
                time_col='_time',
                value_col='_value',
                title='Heat Pump Water Heater Power Consumption',
                ylabel='Power',
                unit='watts',
                color='#BAE1FF'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('indoor-temp-timeseries', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('indoor-time-range', 'value')
)
def update_indoor_temp_timeseries(n, time_range):
    """Plot indoor temperature time series."""
    try:
        indoor_df = db.get_indoor_temperature(start_time=time_range)

        if not indoor_df.empty:
            return plot_timeseries(
                indoor_df,
                time_col='_time',
                value_col='_value',
                title='Indoor Temperature Time Series',
                ylabel='Temperature',
                unit='celsius',
                color='#FF6B6B'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('indoor-humidity-timeseries', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('indoor-time-range', 'value')
)
def update_indoor_humidity(n, time_range):
    """Plot indoor humidity time series."""
    try:
        humidity_df = db.get_indoor_humidity(start_time=time_range)

        if not humidity_df.empty:
            return plot_timeseries(
                humidity_df,
                time_col='_time',
                value_col='_value',
                title='Indoor Humidity Time Series',
                ylabel='Humidity',
                unit='percent',
                color='#4ECDC4'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('energy-consumption-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('energy-consumption-time-range', 'value')
)
def update_energy_consumption(n, time_range):
    """Plot energy consumption over time."""
    try:
        # Get temperature data
        indoor_df = db.get_indoor_temperature(start_time=time_range)
        outdoor_df = db.get_outdoor_temperature(start_time=time_range)

        # If outdoor data not available, simulate it
        if outdoor_df.empty and not indoor_df.empty:
            start_time = indoor_df['_time'].min()
            end_time = indoor_df['_time'].max()
            outdoor_df = simulate_outdoor_temperature(start_time, end_time)

        if not indoor_df.empty and not outdoor_df.empty:
            # Calculate energy consumption
            energy_df = energy_calc.calculate_energy_consumption(indoor_df, outdoor_df)

            # Plot time series
            return plot_timeseries(
                energy_df,
                time_col='_time',
                value_col='energy',
                title='House Energy Consumption Over Time',
                ylabel='Energy',
                unit='kwatth',
                color='#4ECDC4'
            )
        else:
            return create_error_figure("No data available")
    except Exception as e:
        return create_error_figure(f"Error: {str(e)}")


@app.callback(
    Output('total-energy-stat', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('energy-metrics-time-range', 'value')
)
def update_total_energy(n, time_range):
    """Plot total energy savings (actual - model)."""
    try:
        # Get actual energy consumption from grid
        actual_kwh = db.get_actual_energy_consumption(start_time=time_range)

        # Get temperature data for model prediction
        indoor_df = db.get_indoor_temperature(start_time=time_range)
        outdoor_df = db.get_outdoor_temperature(start_time=time_range)

        # Simulate outdoor if needed
        if outdoor_df.empty and not indoor_df.empty:
            start_time = indoor_df['_time'].min()
            end_time = indoor_df['_time'].max()
            outdoor_df = simulate_outdoor_temperature(start_time, end_time)

        if not indoor_df.empty and not outdoor_df.empty and actual_kwh > 0:
            # Get model prediction
            metrics = energy_calc.calculate_all_metrics(indoor_df, outdoor_df)
            model_kwh = metrics['total_energy_kwh']
            model_cost = metrics['cost_usd']

            # Calculate actual cost
            actual_cost = energy_calc.calculate_cost(actual_kwh)

            # Calculate savings: model - actual
            savings_kwh = model_kwh - actual_kwh
            cost_savings = model_cost - actual_cost

            # Create figure with calculation breakdown
            fig = plot_stat(
                savings_kwh,
                title='Total Energy Savings',
                unit='kwatth',
                color='#73BF69' if savings_kwh > 0 else '#E02F44'
            )

            # Add cost savings annotation (below kWh value)
            fig.add_annotation(
                text=f'<b>Cost Savings: ${cost_savings:.2f}</b>',
                xref="paper", yref="paper",
                x=0.5, y=0.35,
                showarrow=False,
                font=dict(size=14, color='#73BF69' if cost_savings > 0 else '#E02F44'),
                align='center'
            )

            # Add energy calculation breakdown as annotation (at bottom)
            fig.add_annotation(
                text=f'Average House: {model_kwh:.1f} kWh<br>Actual: {actual_kwh:.1f} kWh<br>Savings: {savings_kwh:.1f} kWh',
                xref="paper", yref="paper",
                x=0.5, y=0.05,
                showarrow=False,
                font=dict(size=11, color='#2c3e50'),
                align='center'
            )

            return fig
        else:
            return plot_stat(
                0,
                title='Total Energy Savings\nActual - Average House',
                unit='kwatth',
                color='#888888'
            )
    except Exception as e:
        return plot_stat(
            0,
            title='Total Energy Savings\nActual - Average House',
            unit='kwatth',
            color='#E02F44'
        )


@app.callback(
    Output('total-cost-gauge', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('energy-metrics-time-range', 'value')
)
def update_total_cost(n, time_range):
    """Plot total energy cost bar gauge."""
    try:
        # Get temperature data
        indoor_df = db.get_indoor_temperature(start_time=time_range)
        outdoor_df = db.get_outdoor_temperature(start_time=time_range)

        # Simulate outdoor if needed
        if outdoor_df.empty and not indoor_df.empty:
            start_time = indoor_df['_time'].min()
            end_time = indoor_df['_time'].max()
            outdoor_df = simulate_outdoor_temperature(start_time, end_time)

        if not indoor_df.empty and not outdoor_df.empty:
            # Calculate model energy cost
            metrics = energy_calc.calculate_all_metrics(indoor_df, outdoor_df)
            model_cost = metrics['cost_usd']

            # Calculate actual energy cost
            actual_kwh = db.get_actual_energy_consumption(start_time=time_range)
            actual_cost = energy_calc.calculate_cost(actual_kwh)

            return plot_bar_gauge(
                ['Average House Energy Cost', 'Actual Energy Cost'],
                [model_cost, actual_cost],
                title='Total Energy Cost',
                unit='currencyUSD',
                horizontal=True,
                colors=['#FF6B6B', '#4ECDC4']
            )
        else:
            return plot_bar_gauge(
                ['Average House Energy Cost', 'Actual Energy Cost'],
                [0, 0],
                title='Total Energy Cost',
                unit='currencyUSD',
                horizontal=True,
                colors=['#888888', '#888888']
            )
    except Exception as e:
        return plot_bar_gauge(
            ['Average House Energy Cost', 'Actual Energy Cost'],
            [0, 0],
            title='Total Energy Cost',
            unit='currencyUSD',
            horizontal=True,
            colors=['#E02F44']
        )


@app.callback(
    Output('co2-emissions-stat', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('energy-metrics-time-range', 'value')
)
def update_co2_emissions(n, time_range):
    """Plot CO2 emissions stat."""
    try:
        # Get actual energy consumption from grid
        actual_kwh = db.get_actual_energy_consumption(start_time=time_range)

        # Get temperature data
        indoor_df = db.get_indoor_temperature(start_time=time_range)
        outdoor_df = db.get_outdoor_temperature(start_time=time_range)

        # Simulate outdoor if needed
        if outdoor_df.empty and not indoor_df.empty:
            start_time = indoor_df['_time'].min()
            end_time = indoor_df['_time'].max()
            outdoor_df = simulate_outdoor_temperature(start_time, end_time)

        if not indoor_df.empty and not outdoor_df.empty and actual_kwh > 0:
            metrics = energy_calc.calculate_all_metrics(indoor_df, outdoor_df)
            model_kwh = metrics['total_energy_kwh']

            # Calculate savings: model - actual
            savings_kwh = model_kwh - actual_kwh

            # Calculate equivalent km driven
            equivalent_km = metrics['equivalent_km']

            # Create custom figure with message
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=[0], y=[0],
                mode='markers',
                marker=dict(size=0.1, color='rgba(0,0,0,0)'),
                showlegend=False,
                hoverinfo='skip'
            ))

            # Add title
            fig.add_annotation(
                x=0.5, y=0.75,
                text="<b>Energy Savings Impact</b>",
                showarrow=False,
                font=dict(size=16, color='#2c3e50'),
                xref='paper', yref='paper',
                xanchor='center', yanchor='middle'
            )

            # Add main message with better formatting
            fig.add_annotation(
                x=0.5, y=0.5,
                text=f"<b style='font-size:28px'>{savings_kwh:.1f} kWh</b>",
                showarrow=False,
                font=dict(size=28, color='#FF9933'),
                xref='paper', yref='paper',
                xanchor='center', yanchor='middle'
            )

            # Add explanation text
            fig.add_annotation(
                x=0.5, y=0.3,
                text=f"can drive a car for",
                showarrow=False,
                font=dict(size=14, color='#555555'),
                xref='paper', yref='paper',
                xanchor='center', yanchor='middle'
            )

            # Add distance value
            fig.add_annotation(
                x=0.5, y=0.1,
                text=f"<b style='font-size:32px'>{equivalent_km:.1f} km</b>",
                showarrow=False,
                font=dict(size=32, color='#4ECDC4'),
                xref='paper', yref='paper',
                xanchor='center', yanchor='middle'
            )

            fig.update_layout(
                xaxis=dict(visible=False, range=[0, 1]),
                yaxis=dict(visible=False, range=[0, 1]),
                margin=dict(l=0, r=0, t=0, b=0),
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                autosize=True
            )

            return fig
        else:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=[0], y=[0],
                mode='markers',
                marker=dict(size=0.1, color='rgba(0,0,0,0)'),
                showlegend=False,
                hoverinfo='skip'
            ))

            fig.add_annotation(
                x=0.5, y=0.5,
                text="<b>No data available</b>",
                showarrow=False,
                font=dict(size=18, color='#888888'),
                xref='paper', yref='paper',
                xanchor='center', yanchor='middle'
            )

            fig.update_layout(
                xaxis=dict(visible=False, range=[0, 1]),
                yaxis=dict(visible=False, range=[0, 1]),
                margin=dict(l=0, r=0, t=0, b=0),
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                autosize=True
            )

            return fig
    except Exception as e:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(size=0.1, color='rgba(0,0,0,0)'),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"<b>Error: {str(e)}</b>",
            showarrow=False,
            font=dict(size=14, color='#E02F44'),
            xref='paper', yref='paper',
            xanchor='center', yanchor='middle'
        )

        fig.update_layout(
            xaxis=dict(visible=False, range=[0, 1]),
            yaxis=dict(visible=False, range=[0, 1]),
            margin=dict(l=0, r=0, t=0, b=0),
            height=350,
            plot_bgcolor='white',
            paper_bgcolor='white',
            autosize=True
        )

        return fig


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_error_figure(message):
    """Create a figure displaying an error message."""
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="red"),
        xanchor='center',
        yanchor='middle'
    )

    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        height=300
    )

    return fig


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("DC HOUSE DASHBOARD - PLOTLY DASH VERSION")
    print("=" * 80)
    print("\nStarting Dash server...")
    print("Dashboard will be available at: http://localhost:8050")
    print("Or access from other devices at: http://YOUR_IP:8050")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80)

    app.run(debug=True, host='0.0.0.0', port=8050)
