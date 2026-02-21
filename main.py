# main dashboard
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# import graphs defined in visualizations.py, queries from queries.py, and mpc calculation from mpc.py
from queries import InfluxDBHelper
from visualizations import (
    plot_timeseries, plot_multi_timeseries, plot_bar_chart,
    plot_gauge, plot_stat, plot_bar_gauge, plot_pie_chart
)
from energy_savings import EnergyCalculator, simulate_outdoor_temperature


# CONFIGURATION
INFLUX_CONFIG = {
    'url': 'http://159.203.70.114:8086',
    'token': 'ppl7TgaEtWrzrnO3PzNl3IResAeisDrU32bHsVXPHNZeMmGM7-s-N5U98NrYoArkdEOIHa6R8qKOy_4SyJO46g==',
    'org': 'dchouse'
}

# Dashboard time ranges
# TODO - get user input with selection menu for time ranges
TIME_RANGES = {
    'default': '-7d',
    'energy_bill': '-30d',
    'mpc_savings': '-30d',
}

# dashboard builder
class DCHouseDashboard:

    def __init__(self, influx_config):
        # connect to db
        self.db = InfluxDBHelper(**influx_config)
        self.energy_calc = EnergyCalculator()

    def build_full_dashboard(self):
        """Build the complete dashboard with all panels."""
        # Create figure with grid layout
        fig = plt.figure(figsize=(20, 24))
        fig.suptitle('DC House Nanogrid Dashboard', fontsize=20,
                    fontweight='bold', y=0.995)

        # Create grid spec for layout (similar to Grafana rows)
        gs = gridspec.GridSpec(7, 4, figure=fig, hspace=0.4, wspace=0.3,
                              top=0.98, bottom=0.02, left=0.05, right=0.95)

        # ---------------------------------------------------------
        # Row 1 -- High Level Overview
        print("Building High Level Overview...")

        # Outdoor vs Indoor Temperature (time series)
        ax_temp = fig.add_subplot(gs[0, :2])
        self._plot_outdoor_indoor_temp(ax_temp)

        # Energy Bill Gauge
        ax_bill = fig.add_subplot(gs[0, 2])
        self._plot_energy_bill_gauge(ax_bill)

        # Device Usage Pie Chart
        ax_pie = fig.add_subplot(gs[0, 3])
        self._plot_device_usage_pie(ax_pie)

        # ---------------------------------------------------------
        # Row 2 -- Energy Usage
        print("Building Energy Usage section...")

        # Energy usage over time
        ax_energy = fig.add_subplot(gs[1, :])
        self._plot_energy_usage_timeseries(ax_energy)

        # ---------------------------------------------------------
        # ROW 3: Heat Pumps
        print("Building Heat Pumps section...")

        # Air Source Heat Pump Temperature
        ax_hp_temp = fig.add_subplot(gs[2, :2])
        self._plot_heat_pump_temp(ax_hp_temp)

        # Air Source Heat Pump Power
        ax_hp_power = fig.add_subplot(gs[2, 2:])
        self._plot_heat_pump_power(ax_hp_power)

        # HP Water Heater Temperature
        ax_hpwh_temp = fig.add_subplot(gs[3, :2])
        self._plot_hp_water_heater_temp(ax_hpwh_temp)

        # HP Water Heater Power
        ax_hpwh_power = fig.add_subplot(gs[3, 2:])
        self._plot_hp_water_heater_power(ax_hpwh_power)

        # ---------------------------------------------------------
        # ROW 4: Indoor Environment
        print("Building Indoor Environment section...")

        # Indoor Temperature Time Series
        ax_indoor_temp = fig.add_subplot(gs[4, :2])
        self._plot_indoor_temp_timeseries(ax_indoor_temp)

        # Indoor Humidity Time Series
        ax_indoor_humidity = fig.add_subplot(gs[4, 2:])
        self._plot_indoor_humidity_timeseries(ax_indoor_humidity)

        # ---------------------------------------------------------
        # ROW 5 & 6: Energy Analysis
        print("Building Energy Analysis section...")

        # Energy Consumption Time Series
        ax_energy_consumption = fig.add_subplot(gs[5, :])
        self._plot_energy_consumption(ax_energy_consumption)

        # Total Energy (stat)
        ax_total_energy = fig.add_subplot(gs[6, 0])
        self._plot_total_energy_stat(ax_total_energy)

        # Energy Cost (bar gauge)
        ax_energy_cost = fig.add_subplot(gs[6, 1:3])
        self._plot_energy_cost(ax_energy_cost)

        # CO2 Emissions (stat)
        ax_co2_emissions = fig.add_subplot(gs[6, 3])
        self._plot_co2_emissions(ax_co2_emissions)

        print("Dashboard complete!")
        return fig

    # ---------------------------------------------------------
    # plotting methods to use in the build_dashboard method above
    # each method: queries the db, processes data, calls function from visualizations.py, and has error handling
    def _plot_outdoor_indoor_temp(self, ax):
        """Plot outdoor vs indoor temperature comparison."""
        try:
            indoor_df = self.db.get_indoor_temperature(start_time=TIME_RANGES['default'])
            # Note: Outdoor temp query may need adjustment based on your data
            # Using simulated data if not available
            if indoor_df.empty:
                print("  Warning: No indoor temperature data available")
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("Outdoor vs. Indoor Temperature", fontweight='bold')
                return

            # For demo, we'll just plot indoor temperature
            # You can add outdoor temperature when available
            plot_timeseries(ax, indoor_df, time_col='_time', value_col='_value',
                          title='Indoor Temperature',
                          ylabel='Temperature', unit='fahrenheit',
                          color='#FF6B6B')

        except Exception as e:
            print(f"  Error plotting temperature: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_energy_bill_gauge(self, ax):
        """Plot predicted energy bill gauge."""
        try:
            bill_df = self.db.get_predicted_energy_bill(start_time=TIME_RANGES['energy_bill'])

            if not bill_df.empty and 'value' in bill_df.columns:
                bill_value = bill_df['value'].iloc[0]
            else:
                # Estimate based on grid power
                power_df = self.db.get_grid_power(start_time=TIME_RANGES['energy_bill'])
                if not power_df.empty:
                    total_kwh = power_df['_value'].sum() / 1000
                    bill_value = total_kwh * 0.15
                else:
                    bill_value = 0

            plot_gauge(ax, bill_value, title='Last 30 Days Predicted Energy Bill',
                      unit='currencyUSD', min_val=0, max_val=300,
                      thresholds=[0, 100, 200, 300],
                      threshold_colors=['#73BF69', '#F2CC0C', '#FF9933', '#E02F44'])

        except Exception as e:
            print(f"  Error plotting energy bill: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_device_usage_pie(self, ax):
        """Plot device energy usage pie chart."""
        try:
            device_df = self.db.get_energy_usage_by_device(start_time=TIME_RANGES['energy_bill'])

            if not device_df.empty and '_measurement' in device_df.columns:
                # Group by device and sum
                device_totals = device_df.groupby('_measurement')['_value'].sum()
                # Get top 5 devices
                top_devices = device_totals.nlargest(5)

                # Convert from Wh to kWh
                top_devices_kwh = top_devices / 1000

                plot_pie_chart(ax, list(top_devices_kwh.index), list(top_devices_kwh.values),
                             title='Device Energy Usage',
                             unit='kwatth', show_percentages=True)
            else:
                # Show sample data if no real data
                labels = ['HVAC', 'Water Heater', 'Appliances', 'Lighting', 'Other']
                values = [45, 20, 15, 10, 10]
                plot_pie_chart(ax, labels, values, title='Device Energy Usage',
                             unit='percent', show_percentages=True)

        except Exception as e:
            print(f"  Error plotting device usage: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_energy_usage_timeseries(self, ax):
        """Plot energy usage over time."""
        try:
            power_df = self.db.get_grid_power(start_time=TIME_RANGES['default'])

            if not power_df.empty:
                # Convert power to energy (kWh)
                power_df['_value'] = power_df['_value'] / 1000  # Convert to kW

                plot_timeseries(ax, power_df, time_col='_time', value_col='_value',
                              title='Energy Usage Over Time',
                              ylabel='Power', unit='kwatth',
                              color='#4ECDC4')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)

        except Exception as e:
            print(f"  Error plotting energy usage: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_heat_pump_temp(self, ax):
        """Plot heat pump temperature time series."""
        try:
            hp_temp_df = self.db.get_heat_pump_temperature(start_time=TIME_RANGES['default'])

            if not hp_temp_df.empty:
                plot_timeseries(ax, hp_temp_df, time_col='_time', value_col='_value',
                              title='Heat Pump Temperature Time Series',
                              ylabel='Temperature', unit='fahrenheit',
                              color='#FF6B6B')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("Heat Pump Temperature Time Series", fontweight='bold')

        except Exception as e:
            print(f"  Error plotting heat pump temp: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_heat_pump_power(self, ax):
        """Plot heat pump power consumption."""
        try:
            hp_power_df = self.db.get_heat_pump_power(start_time=TIME_RANGES['default'])

            if not hp_power_df.empty:
                plot_timeseries(ax, hp_power_df, time_col='_time', value_col='_value',
                              title='Air Source Heat Pump Power Consumption',
                              ylabel='Power', unit='watts',
                              color='#95E1D3')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("Air Source Heat Pump Power Consumption", fontweight='bold')

        except Exception as e:
            print(f"  Error plotting heat pump power: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_hp_water_heater_temp(self, ax):
        """Plot HP water heater temperature time series."""
        try:
            hpwh_temp_df = self.db.get_hp_water_heater_temperature(start_time=TIME_RANGES['default'])

            if not hpwh_temp_df.empty:
                plot_timeseries(ax, hpwh_temp_df, time_col='_time', value_col='_value',
                              title='HP Water Heater Temperature Time Series',
                              ylabel='Temperature', unit='fahrenheit',
                              color='#FFB6B9')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("HP Water Heater Temperature Time Series", fontweight='bold')

        except Exception as e:
            print(f"  Error plotting HPWH temp: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_hp_water_heater_power(self, ax):
        """Plot HP water heater power consumption."""
        try:
            hpwh_power_df = self.db.get_hp_water_heater_power(start_time=TIME_RANGES['default'])

            if not hpwh_power_df.empty:
                plot_timeseries(ax, hpwh_power_df, time_col='_time', value_col='_value',
                              title='HP Water Heater Power Consumption',
                              ylabel='Power', unit='watts',
                              color='#BAE1FF')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("HP Water Heater Power Consumption", fontweight='bold')

        except Exception as e:
            print(f"  Error plotting HPWH power: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_indoor_temp_timeseries(self, ax):
        """Plot indoor temperature time series."""
        try:
            indoor_df = self.db.get_indoor_temperature(start_time=TIME_RANGES['default'])

            if not indoor_df.empty:
                plot_timeseries(ax, indoor_df, time_col='_time', value_col='_value',
                              title='Indoor Temperature Time Series',
                              ylabel='Temperature', unit='fahrenheit',
                              color='#FF6B6B')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("Indoor Temperature Time Series", fontweight='bold')

        except Exception as e:
            print(f"  Error plotting indoor temp: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_indoor_humidity_timeseries(self, ax):
        """Plot indoor humidity time series."""
        try:
            humidity_df = self.db.get_indoor_humidity(start_time=TIME_RANGES['default'])

            if not humidity_df.empty:
                plot_timeseries(ax, humidity_df, time_col='_time', value_col='_value',
                              title='Indoor Humidity Time Series',
                              ylabel='Humidity', unit='percent',
                              color='#4ECDC4')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("Indoor Humidity Time Series", fontweight='bold')

        except Exception as e:
            print(f"  Error plotting humidity: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_energy_consumption(self, ax):
        """Plot energy consumption time series."""
        try:
            # Get temperature data
            indoor_df = self.db.get_indoor_temperature(start_time=TIME_RANGES['mpc_savings'])
            outdoor_df = self.db.get_outdoor_temperature(start_time=TIME_RANGES['mpc_savings'])

            # If outdoor data not available, simulate it
            if outdoor_df.empty and not indoor_df.empty:
                start_time = indoor_df['_time'].min()
                end_time = indoor_df['_time'].max()
                outdoor_df = simulate_outdoor_temperature(start_time, end_time)

            if not indoor_df.empty and not outdoor_df.empty:
                # Calculate energy consumption
                energy_df = self.energy_calc.calculate_energy_consumption(indoor_df, outdoor_df)

                # Plot time series
                plot_timeseries(ax, energy_df,
                              time_col='_time', value_col='energy',
                              title='House Energy Consumption Over Time',
                              ylabel='Energy', unit='kwatth',
                              color='#4ECDC4')
            else:
                ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title("House Energy Consumption Over Time", fontweight='bold')

        except Exception as e:
            print(f"Error plotting energy consumption: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

    def _plot_total_energy_stat(self, ax):
        """Plot total energy savings (actual - model)."""
        try:
            # Get actual energy consumption from grid
            actual_kwh = self.db.get_actual_energy_consumption(start_time=TIME_RANGES['mpc_savings'])

            # Get temperature data for model prediction
            indoor_df = self.db.get_indoor_temperature(start_time=TIME_RANGES['mpc_savings'])
            outdoor_df = self.db.get_outdoor_temperature(start_time=TIME_RANGES['mpc_savings'])

            # Simulate outdoor if needed
            if outdoor_df.empty and not indoor_df.empty:
                start_time = indoor_df['_time'].min()
                end_time = indoor_df['_time'].max()
                outdoor_df = simulate_outdoor_temperature(start_time, end_time)

            if not indoor_df.empty and not outdoor_df.empty and actual_kwh > 0:
                # Get model prediction
                metrics = self.energy_calc.calculate_all_metrics(indoor_df, outdoor_df)
                model_kwh = metrics['total_energy_kwh']

                # Calculate savings: model - actual
                savings_kwh = model_kwh - actual_kwh

                color = '#73BF69' if savings_kwh > 0 else '#E02F44'
                plot_stat(ax, savings_kwh,
                         title='Total Energy Savings',
                         unit='kwatth', color=color)

                # Add calculation breakdown as text below the main value
                ax.text(0.5, 0.1,
                       f'Model: {model_kwh:.2f} kWh\nActual: {actual_kwh:.2f} kWh\nSavings: {savings_kwh:.2f} kWh',
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=10, color='#2c3e50')
            else:
                plot_stat(ax, 0, title='Total Energy Savings\nActual - Model',
                         unit='kwatth', color='#888888')

        except Exception as e:
            print(f"  Error plotting total energy savings: {e}")
            plot_stat(ax, 0, title='Total Energy Savings\nActual - Model',
                     unit='kwatth', color='#E02F44')

    def _plot_energy_cost(self, ax):
        """Plot energy cost bar gauge."""
        try:
            # Get temperature data
            indoor_df = self.db.get_indoor_temperature(start_time=TIME_RANGES['mpc_savings'])
            outdoor_df = self.db.get_outdoor_temperature(start_time=TIME_RANGES['mpc_savings'])

            # Simulate outdoor if needed
            if outdoor_df.empty and not indoor_df.empty:
                start_time = indoor_df['_time'].min()
                end_time = indoor_df['_time'].max()
                outdoor_df = simulate_outdoor_temperature(start_time, end_time)

            if not indoor_df.empty and not outdoor_df.empty:
                # Calculate model energy cost
                metrics = self.energy_calc.calculate_all_metrics(indoor_df, outdoor_df)
                model_cost = metrics['cost_usd']

                # Calculate actual energy cost
                actual_kwh = self.db.get_actual_energy_consumption(start_time=TIME_RANGES['mpc_savings'])
                actual_cost = self.energy_calc.calculate_cost(actual_kwh)

                plot_bar_gauge(ax, ['Model Energy Cost', 'Actual Energy Cost'],
                             [model_cost, actual_cost],
                             title='Total Energy Cost',
                             unit='currencyUSD', horizontal=True,
                             colors=['#FF6B6B', '#4ECDC4'])
            else:
                plot_bar_gauge(ax, ['Model Energy Cost', 'Actual Energy Cost'],
                             [0, 0],
                             title='Total Energy Cost',
                             unit='currencyUSD', horizontal=True,
                             colors=['#888888', '#888888'])

        except Exception as e:
            print(f"  Error plotting energy cost: {e}")
            plot_bar_gauge(ax, ['Model Energy Cost', 'Actual Energy Cost'],
                         [0, 0],
                         title='Total Energy Cost',
                         unit='currencyUSD', horizontal=True,
                         colors=['#E02F44', '#E02F44'])

    def _plot_co2_emissions(self, ax):
        """Plot CO2 emissions stat."""
        try:
            # Get temperature data
            indoor_df = self.db.get_indoor_temperature(start_time=TIME_RANGES['mpc_savings'])
            outdoor_df = self.db.get_outdoor_temperature(start_time=TIME_RANGES['mpc_savings'])

            # Simulate outdoor if needed
            if outdoor_df.empty and not indoor_df.empty:
                start_time = indoor_df['_time'].min()
                end_time = indoor_df['_time'].max()
                outdoor_df = simulate_outdoor_temperature(start_time, end_time)

            if not indoor_df.empty and not outdoor_df.empty:
                metrics = self.energy_calc.calculate_all_metrics(indoor_df, outdoor_df)

                plot_stat(ax, metrics['equivalent_km'],
                         title='CO2 Emissions Equivalent to\nDriving a Car For:',
                         unit='lengthkm', color='#FF9933')
            else:
                plot_stat(ax, 0, title='CO2 Emissions Equivalent to\nDriving a Car For:',
                         unit='lengthkm', color='#888888')

        except Exception as e:
            print(f"  Error plotting CO2 emissions: {e}")
            plot_stat(ax, 0, title='CO2 Emissions Equivalent to\nDriving a Car For:',
                     unit='lengthkm', color='#E02F44')

    # close connection to db
    def close(self):
        self.db.close()


# main execution
def main():
    # updates to terminal
    print("=" * 80)
    print("DC HOUSE DASHBOARD")
    print("=" * 80)
    print("\nConnecting to InfluxDB...")

    # Create dashboard
    dashboard = DCHouseDashboard(INFLUX_CONFIG)

    print("Building dashboard...")
    fig = dashboard.build_full_dashboard()

    # save to png file
    print("\nSaving dashboard...")
    fig.savefig('dc_house_dashboard.png', dpi=150, bbox_inches='tight')
    print("Dashboard saved as 'dc_house_dashboard.png'")

    # opens window showing dashboard
    print("\nDisplaying dashboard...")
    plt.show()

    # Clean up
    dashboard.close()
    print("\nDashboard complete!")


if __name__ == '__main__':
    main()
