"""
Dashboard Visualization Library - Plotly Version
Modular functions for creating different chart types from InfluxDB data.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np


# ============================================================================
# TIME SERIES CHARTS
# ============================================================================

def plot_timeseries(df, time_col='_time', value_col='_value',
                   title='', ylabel='', unit='', color='#1f77b4',
                   show_grid=True, aggregate=None, yaxis_range=None):
    """
    Plot a time series chart.

    Parameters:
    -----------
    df : pandas DataFrame
        Data with time and value columns
    time_col : str
        Name of the time column
    value_col : str
        Name of the value column
    title : str
        Chart title
    ylabel : str
        Y-axis label
    unit : str
        Unit of measurement (e.g., 'celsius', 'watts', 'kilowatts')
    color : str
        Line color
    show_grid : bool
        Whether to show grid lines
    aggregate : str or None
        Aggregation method if needed ('mean', 'sum', 'max', 'min')
    yaxis_range : tuple or None
        Y-axis range as (min, max). If None, starts at 0 with auto max.

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    # Ensure time column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col])

    # Sort by time
    df = df.sort_values(time_col)

    # Apply aggregation if specified
    if aggregate:
        df = df.set_index(time_col)
        if aggregate == 'mean':
            df = df[value_col].resample('1H').mean()
        elif aggregate == 'sum':
            df = df[value_col].resample('1H').sum()
        elif aggregate == 'max':
            df = df[value_col].resample('1H').max()
        elif aggregate == 'min':
            df = df[value_col].resample('1H').min()
        df = df.reset_index()
        time_col = 'index'

    # Auto-convert watts to kilowatts if values are large
    data_values = df[value_col].copy()
    if unit == 'watts' and data_values.max() > 1000:
        data_values = data_values / 1000
        unit = 'kilowatts'

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[time_col],
        y=data_values,
        mode='lines',
        line=dict(color=color, width=2),
        hovertemplate='%{x}<br>%{y:.1f}<extra></extra>'
    ))

    # Add unit to y-axis label if provided
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'kilowatts': 'kW',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
    }
    unit_label = unit_map.get(unit, unit)

    ylabel_with_unit = ylabel
    if unit_label:
        ylabel_with_unit = f"{ylabel} ({unit_label})" if ylabel else unit_label

    # Update layout
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='black')),
        xaxis_title='Time',
        yaxis_title=ylabel_with_unit,
        showlegend=False,
        hovermode='x unified',
        template='plotly_white',
        margin=dict(l=50, r=30, t=50, b=50)
    )

    if show_grid:
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    # Set y-axis range (default starts at 0)
    if yaxis_range:
        fig.update_yaxes(range=yaxis_range)
    else:
        fig.update_yaxes(rangemode='tozero')

    return fig


def plot_multi_timeseries(data_list, time_col='_time', value_col='_value',
                         title='', ylabel='', unit='', labels=None,
                         colors=None, show_grid=True, show_legend=True):
    """
    Plot multiple time series on the same chart.

    Parameters:
    -----------
    data_list : list of DataFrames
        List of dataframes to plot
    time_col : str
        Name of the time column
    value_col : str
        Name of the value column
    title : str
        Chart title
    ylabel : str
        Y-axis label
    unit : str
        Unit of measurement
    labels : list of str
        Labels for each series
    colors : list of str
        Colors for each series
    show_grid : bool
        Whether to show grid lines
    show_legend : bool
        Whether to show legend

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    if labels is None:
        labels = [f'Series {i+1}' for i in range(len(data_list))]

    if colors is None:
        colors = px.colors.qualitative.Plotly

    # Create figure
    fig = go.Figure()

    # Plot each series
    for i, (df, label, color) in enumerate(zip(data_list, labels, colors)):
        # Ensure time column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col])

        df = df.sort_values(time_col)

        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[value_col],
            mode='lines',
            name=label,
            line=dict(color=color, width=2),
            hovertemplate='%{x}<br>%{y:.2f}<extra></extra>'
        ))

    # Add unit to y-axis label if provided
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
    }
    unit_label = unit_map.get(unit, unit)

    ylabel_with_unit = ylabel
    if unit_label:
        ylabel_with_unit = f"{ylabel} ({unit_label})" if ylabel else unit_label

    # Update layout
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='black')),
        xaxis_title='Time',
        yaxis_title=ylabel_with_unit,
        showlegend=show_legend,
        hovermode='x unified',
        template='plotly_white',
        margin=dict(l=50, r=30, t=50, b=50)
    )

    if show_grid:
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


# ============================================================================
# BAR CHARTS
# ============================================================================

def plot_bar_chart(df, x_col, y_col, title='', xlabel='', ylabel='',
                  unit='', color='#1f77b4', show_grid=True, horizontal=False):
    """
    Plot a bar chart.

    Parameters:
    -----------
    df : pandas DataFrame
        Data with x and y columns
    x_col : str
        Name of the x column (categories)
    y_col : str
        Name of the y column (values)
    title : str
        Chart title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    unit : str
        Unit of measurement
    color : str
        Bar color
    show_grid : bool
        Whether to show grid lines
    horizontal : bool
        Whether to plot horizontal bars

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    # Add unit to labels if provided
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
    }
    unit_label = unit_map.get(unit, unit)

    fig = go.Figure()

    if horizontal:
        fig.add_trace(go.Bar(
            x=df[y_col],
            y=df[x_col],
            orientation='h',
            marker=dict(color=color),
            hovertemplate='%{y}: %{x:.2f}<extra></extra>'
        ))
        xlabel_final = f"{ylabel} ({unit_label})" if ylabel and unit_label else ylabel
        ylabel_final = xlabel
    else:
        fig.add_trace(go.Bar(
            x=df[x_col],
            y=df[y_col],
            marker=dict(color=color),
            hovertemplate='%{x}: %{y:.2f}<extra></extra>'
        ))
        xlabel_final = xlabel
        ylabel_final = f"{ylabel} ({unit_label})" if ylabel and unit_label else ylabel

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='black')),
        xaxis_title=xlabel_final,
        yaxis_title=ylabel_final,
        showlegend=False,
        template='plotly_white',
        margin=dict(l=50, r=30, t=50, b=50)
    )

    if show_grid:
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


# ============================================================================
# GAUGE/STAT PANELS
# ============================================================================

def plot_gauge(value, title='', unit='', min_val=0, max_val=100,
              thresholds=None, threshold_colors=None):
    """
    Plot a gauge chart.

    Parameters:
    -----------
    value : float
        Current value to display
    title : str
        Chart title
    unit : str
        Unit of measurement
    min_val : float
        Minimum value on gauge
    max_val : float
        Maximum value on gauge
    thresholds : list of float
        Threshold values for color zones
    threshold_colors : list of str
        Colors for each threshold zone

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    # Default thresholds if not provided
    if thresholds is None:
        thresholds = [min_val, (max_val - min_val) * 0.5 + min_val, max_val]
    if threshold_colors is None:
        threshold_colors = ['#73BF69', '#F2CC0C', '#E02F44']

    # Map unit to symbol
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
    }
    unit_label = unit_map.get(unit, unit)

    # Create steps for color zones
    steps = []
    for i in range(len(thresholds) - 1):
        steps.append({
            'range': [thresholds[i], thresholds[i + 1]],
            'color': threshold_colors[i]
        })

    # Format number with prefix for currency, suffix for others
    number_format = {}
    if unit == 'currencyUSD':
        number_format = {'prefix': f"{unit_label}"}
    elif unit_label:
        number_format = {'suffix': f" {unit_label}"}

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        number=number_format,
        gauge={
            'axis': {'range': [min_val, max_val]},
            'steps': steps,
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        height=300
    )

    return fig


def plot_stat(value, title='', unit='', subtitle='',
             color='#1f77b4', show_trend=False, trend_value=None):
    """
    Plot a stat panel (single large number).

    Parameters:
    -----------
    value : float
        Value to display
    title : str
        Panel title
    unit : str
        Unit of measurement
    subtitle : str
        Additional text below value
    color : str
        Color for the value
    show_trend : bool
        Whether to show trend indicator
    trend_value : float
        Percentage change (positive or negative)

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    # Map unit to symbol
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
        'lengthkm': 'km',
    }
    unit_label = unit_map.get(unit, unit)

    # Format value based on magnitude (limited sig figs)
    if abs(value) >= 100:
        formatted_value = f"{value:.0f}"
    elif abs(value) >= 10:
        formatted_value = f"{value:.1f}"
    else:
        formatted_value = f"{value:.2f}"

    fig = go.Figure()

    # Add invisible scatter to create the canvas
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(size=0.1, color='rgba(0,0,0,0)'),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Add title
    if title:
        fig.add_annotation(
            x=0.5, y=0.85,
            text=f"<b>{title}</b>",
            showarrow=False,
            font=dict(size=14, color='black'),
            xref='paper', yref='paper',
            xanchor='center', yanchor='top'
        )

    # Add main value
    display_text = f"<b>{formatted_value}{' ' + unit_label if unit_label else ''}</b>"
    fig.add_annotation(
        x=0.5, y=0.5,
        text=display_text,
        showarrow=False,
        font=dict(size=36, color=color),
        xref='paper', yref='paper',
        xanchor='center', yanchor='middle'
    )

    # Add subtitle
    if subtitle:
        fig.add_annotation(
            x=0.5, y=0.25,
            text=subtitle,
            showarrow=False,
            font=dict(size=10, color='gray'),
            xref='paper', yref='paper',
            xanchor='center', yanchor='middle'
        )

    # Add trend
    if show_trend and trend_value is not None:
        trend_color = '#73BF69' if trend_value >= 0 else '#E02F44'
        trend_arrow = '▲' if trend_value >= 0 else '▼'
        trend_text = f"{trend_arrow} {trend_value:+.1f}%"

        fig.add_annotation(
            x=0.5, y=0.15,
            text=trend_text,
            showarrow=False,
            font=dict(size=12, color=trend_color),
            xref='paper', yref='paper',
            xanchor='center', yanchor='middle'
        )

    fig.update_layout(
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        margin=dict(l=20, r=20, t=20, b=20),
        height=250,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    return fig


def plot_bar_gauge(categories, values, title='', unit='',
                  horizontal=True, max_val=None, colors=None):
    """
    Plot a bar gauge (horizontal/vertical bars with values).

    Parameters:
    -----------
    categories : list
        Category names
    values : list
        Values for each category
    title : str
        Chart title
    unit : str
        Unit of measurement
    horizontal : bool
        Whether to plot horizontal bars
    max_val : float
        Maximum value for scaling
    colors : list of str
        Colors for each bar

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    if max_val is None:
        max_val = max(values) * 1.1

    if colors is None:
        colors = ['#1f77b4'] * len(categories)

    # Map unit to symbol
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
        'lengthkm': 'km',
    }
    unit_label = unit_map.get(unit, '')

    fig = go.Figure()

    if horizontal:
        fig.add_trace(go.Bar(
            x=values,
            y=categories,
            orientation='h',
            marker=dict(color=colors),
            text=[f'{v:.1f}{unit_label}' for v in values],
            textposition='outside',
            hovertemplate='%{y}: %{x:.1f}' + unit_label + '<extra></extra>'
        ))
        fig.update_xaxes(range=[0, max_val])
        fig.update_layout(xaxis_title=unit_label)
    else:
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker=dict(color=colors),
            text=[f'{v:.1f}{unit_label}' for v in values],
            textposition='outside',
            hovertemplate='%{x}: %{y:.1f}' + unit_label + '<extra></extra>'
        ))
        fig.update_yaxes(range=[0, max_val])
        fig.update_layout(yaxis_title=unit_label)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='black')),
        showlegend=False,
        template='plotly_white',
        margin=dict(l=50, r=30, t=50, b=50)
    )

    return fig


# ============================================================================
# PIE CHARTS
# ============================================================================

def plot_pie_chart(labels, values, title='', unit='',
                  show_percentages=True, colors=None, explode=None):
    """
    Plot a pie chart.

    Parameters:
    -----------
    labels : list
        Slice labels
    values : list
        Values for each slice
    title : str
        Chart title
    unit : str
        Unit of measurement
    show_percentages : bool
        Whether to show percentages
    colors : list of str
        Colors for each slice
    explode : list of float
        Pull values for each slice (not directly supported in Plotly)

    Returns:
    --------
    plotly.graph_objects.Figure
    """
    # Map unit to symbol
    unit_map = {
        'fahrenheit': '°F',
        'celsius': '°C',
        'watts': 'W',
        'watth': 'Wh',
        'kwatth': 'kWh',
        'percent': '%',
        'currencyUSD': '$',
    }
    unit_label = unit_map.get(unit, unit)

    # Create pie chart
    fig = go.Figure()

    pull_values = explode if explode else [0] * len(labels)

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors) if colors else {},
        pull=pull_values,
        textinfo='percent' if show_percentages else 'value',
        textposition='inside',
        hovertemplate='%{label}<br>%{value:.0f} ' + (unit_label if unit_label else '') + '<br>%{percent}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='black')),
        margin=dict(l=20, r=20, t=50, b=100),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        height=400
    )

    return fig
