"""
Dashboard Visualization Library
Modular functions for creating different chart types from InfluxDB data.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np


# ============================================================================
# TIME SERIES CHARTS
# ============================================================================

def plot_timeseries(ax, df, time_col='_time', value_col='_value',
                   title='', ylabel='', unit='', color='#1f77b4',
                   show_grid=True, aggregate=None):
    """
    Plot a time series chart.

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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
        Unit of measurement (e.g., 'fahrenheit', 'watts')
    color : str
        Line color
    show_grid : bool
        Whether to show grid lines
    aggregate : str or None
        Aggregation method if needed ('mean', 'sum', 'max', 'min')
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

    # Plot
    ax.plot(df[time_col], df[value_col], color=color, linewidth=1.5)

    # Formatting
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlabel('Time', fontsize=10)

    if show_grid:
        ax.grid(True, alpha=0.3, linestyle='--')

    # Format x-axis for dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Add unit to y-axis if provided
    if unit:
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
        current_ylabel = ax.get_ylabel()
        if current_ylabel and unit_label not in current_ylabel:
            ax.set_ylabel(f"{current_ylabel} ({unit_label})")

    return ax


def plot_multi_timeseries(ax, data_list, time_col='_time', value_col='_value',
                         title='', ylabel='', unit='', labels=None,
                         colors=None, show_grid=True, show_legend=True):
    """
    Plot multiple time series on the same chart.

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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
    """
    if labels is None:
        labels = [f'Series {i+1}' for i in range(len(data_list))]

    if colors is None:
        # Use default matplotlib color cycle
        prop_cycle = plt.rcParams['axes.prop_cycle']
        colors = prop_cycle.by_key()['color']

    # Plot each series
    for i, (df, label, color) in enumerate(zip(data_list, labels, colors)):
        # Ensure time column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col])

        df = df.sort_values(time_col)
        ax.plot(df[time_col], df[value_col], color=color,
               linewidth=1.5, label=label)

    # Formatting
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlabel('Time', fontsize=10)

    if show_grid:
        ax.grid(True, alpha=0.3, linestyle='--')

    if show_legend:
        ax.legend(loc='best', fontsize=9, framealpha=0.9)

    # Format x-axis for dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Add unit to y-axis if provided
    if unit:
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
        current_ylabel = ax.get_ylabel()
        if current_ylabel and unit_label not in current_ylabel:
            ax.set_ylabel(f"{current_ylabel} ({unit_label})")

    return ax


# ============================================================================
# BAR CHARTS
# ============================================================================

def plot_bar_chart(ax, df, x_col, y_col, title='', xlabel='', ylabel='',
                  unit='', color='#1f77b4', show_grid=True, horizontal=False):
    """
    Plot a bar chart.

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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
    """
    if horizontal:
        ax.barh(df[x_col], df[y_col], color=color, alpha=0.8)
        ax.set_xlabel(ylabel, fontsize=10)
        ax.set_ylabel(xlabel, fontsize=10)
    else:
        ax.bar(df[x_col], df[y_col], color=color, alpha=0.8)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)

    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)

    if show_grid:
        if horizontal:
            ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        else:
            ax.grid(True, axis='y', alpha=0.3, linestyle='--')

    # Add unit to labels if provided
    if unit:
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

        if horizontal:
            current_xlabel = ax.get_xlabel()
            if current_xlabel and unit_label not in current_xlabel:
                ax.set_xlabel(f"{current_xlabel} ({unit_label})")
        else:
            current_ylabel = ax.get_ylabel()
            if current_ylabel and unit_label not in current_ylabel:
                ax.set_ylabel(f"{current_ylabel} ({unit_label})")

    # Rotate x labels if not horizontal
    if not horizontal:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    return ax


# ============================================================================
# GAUGE/STAT PANELS
# ============================================================================

def plot_gauge(ax, value, title='', unit='', min_val=0, max_val=100,
              thresholds=None, threshold_colors=None):
    """
    Plot a gauge chart (simulated with arc/semicircle).

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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
    """
    # Clear axis
    ax.clear()
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')

    # Default thresholds if not provided
    if thresholds is None:
        thresholds = [min_val, (max_val - min_val) * 0.5 + min_val, max_val]
    if threshold_colors is None:
        threshold_colors = ['#73BF69', '#F2CC0C', '#E02F44']

    # Draw gauge arc
    theta = np.linspace(np.pi, 0, 100)
    x = np.cos(theta)
    y = np.sin(theta)

    # Draw colored zones
    for i in range(len(thresholds) - 1):
        t_start = thresholds[i]
        t_end = thresholds[i + 1]

        # Calculate angles for this zone
        angle_start = np.pi * (1 - (t_start - min_val) / (max_val - min_val))
        angle_end = np.pi * (1 - (t_end - min_val) / (max_val - min_val))

        theta_zone = np.linspace(angle_start, angle_end, 50)
        x_zone_outer = 0.9 * np.cos(theta_zone)
        y_zone_outer = 0.9 * np.sin(theta_zone)
        x_zone_inner = 0.7 * np.cos(theta_zone)
        y_zone_inner = 0.7 * np.sin(theta_zone)

        # Fill the zone
        vertices = list(zip(x_zone_outer, y_zone_outer)) + list(zip(x_zone_inner[::-1], y_zone_inner[::-1]))
        from matplotlib.patches import Polygon
        poly = Polygon(vertices, facecolor=threshold_colors[i], alpha=0.3, edgecolor=threshold_colors[i], linewidth=2)
        ax.add_patch(poly)

    # Draw needle
    value_normalized = (value - min_val) / (max_val - min_val)
    value_normalized = np.clip(value_normalized, 0, 1)
    needle_angle = np.pi * (1 - value_normalized)

    needle_length = 0.8
    needle_x = [0, needle_length * np.cos(needle_angle)]
    needle_y = [0, needle_length * np.sin(needle_angle)]
    ax.plot(needle_x, needle_y, 'k-', linewidth=3)
    ax.plot(0, 0, 'ko', markersize=10)

    # Add value text in center
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

    # Format value text with unit (prefix for currency, suffix for others)
    if unit == 'currencyUSD':
        value_text = f"{unit_label}{value:.1f}"
    elif unit_label:
        value_text = f"{value:.1f} {unit_label}"
    else:
        value_text = f"{value:.1f}"

    ax.text(0, -0.1, value_text, ha='center', va='center',
           fontsize=16, fontweight='bold')

    # Add title
    if title:
        ax.text(0, 1.1, title, ha='center', va='center',
               fontsize=12, fontweight='bold')

    # Add min/max labels
    ax.text(-0.95, 0, f"{min_val:.0f}", ha='center', va='center', fontsize=9)
    ax.text(0.95, 0, f"{max_val:.0f}", ha='center', va='center', fontsize=9)

    return ax


def plot_stat(ax, value, title='', unit='', subtitle='',
             color='#1f77b4', show_trend=False, trend_value=None):
    """
    Plot a stat panel (single large number).

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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
    """
    ax.clear()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

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

    # Format value based on magnitude
    if abs(value) >= 10:
        value_text = f"{value:.0f}"
    else:
        value_text = f"{value:.2f}"

    if unit_label:
        value_text += f" {unit_label}"

    # Display title at top
    if title:
        ax.text(0.5, 0.85, title, ha='center', va='top',
               fontsize=11, fontweight='bold', wrap=True)

    # Display value in center
    ax.text(0.5, 0.5, value_text, ha='center', va='center',
           fontsize=32, fontweight='bold', color=color)

    # Display subtitle at bottom
    if subtitle:
        ax.text(0.5, 0.25, subtitle, ha='center', va='center',
               fontsize=9, style='italic', color='gray')

    # Display trend if requested
    if show_trend and trend_value is not None:
        trend_text = f"{trend_value:+.1f}%"
        trend_color = '#73BF69' if trend_value >= 0 else '#E02F44'
        trend_arrow = '▲' if trend_value >= 0 else '▼'

        ax.text(0.5, 0.15, f"{trend_arrow} {trend_text}", ha='center', va='center',
               fontsize=10, color=trend_color, fontweight='bold')

    return ax


def plot_bar_gauge(ax, categories, values, title='', unit='',
                  horizontal=True, max_val=None, colors=None):
    """
    Plot a bar gauge (horizontal/vertical bars with values).

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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

    if horizontal:
        bars = ax.barh(categories, values, color=colors, alpha=0.8)
        ax.set_xlim(0, max_val)
        ax.set_xlabel(unit_label, fontsize=10)

        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + max_val * 0.02, bar.get_y() + bar.get_height()/2,
                   f'{value:.2f}{unit_label}',
                   va='center', fontsize=9, fontweight='bold')
    else:
        bars = ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_ylim(0, max_val)
        ax.set_ylabel(unit_label, fontsize=10)

        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(bar.get_x() + bar.get_width()/2, value + max_val * 0.02,
                   f'{value:.2f}{unit_label}',
                   ha='center', fontsize=9, fontweight='bold', rotation=0)

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.grid(True, axis='x' if horizontal else 'y', alpha=0.3, linestyle='--')

    return ax


# ============================================================================
# PIE CHARTS
# ============================================================================

def plot_pie_chart(ax, labels, values, title='', unit='',
                  show_percentages=True, colors=None, explode=None):
    """
    Plot a pie chart.

    Parameters:
    -----------
    ax : matplotlib axis
        The axis to plot on
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
        Explode values for each slice
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

    # Create autopct function to show both value and percentage
    def autopct_format(pct, allvals):
        absolute = int(pct/100.*sum(allvals))
        if show_percentages:
            return f'{pct:.1f}%\n({absolute} {unit_label})'
        return f'{absolute} {unit_label}'

    # Plot pie chart
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct=lambda pct: autopct_format(pct, values),
                                       colors=colors, explode=explode, startangle=90)

    # Styling
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(8)
        autotext.set_fontweight('bold')

    for text in texts:
        text.set_fontsize(9)

    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)

    return ax
