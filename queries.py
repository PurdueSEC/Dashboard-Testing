# query InfluxDB and return data formatted for visualization.
from influxdb_client import InfluxDBClient
import pandas as pd
from datetime import datetime, timedelta

# might not need these below
import warnings
from influxdb_client.client.warnings import MissingPivotFunction

# Suppress InfluxDB pivot warnings - we don't need pivot for our use case
warnings.simplefilter("ignore", MissingPivotFunction)


class InfluxDBHelper:
    def __init__(self, url, token, org):
        """
        Initialize InfluxDB client.

        Parameters:
        -----------
        url : str
            InfluxDB URL
        token : str
            Authentication token
        org : str
            Organization name
        """
        self.url = url
        self.token = token
        self.org = org
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()

    def query(self, query_text, bucket=None):
        """
        Execute a Flux query and return results as DataFrame.

        Parameters:
        -----------
        query_text : str
            Flux query string
        bucket : str
            Bucket name (optional, can be in query)

        Returns:
        --------
        pandas DataFrame with query results
        """
        try:
            tables = self.query_api.query_data_frame(org=self.org, query=query_text)

            # Handle multiple tables
            if isinstance(tables, list):
                if len(tables) == 0:
                    return pd.DataFrame()
                df = pd.concat(tables, ignore_index=True)
            else:
                df = tables

            # Convert _time to datetime if present
            if '_time' in df.columns:
                df['_time'] = pd.to_datetime(df['_time'])

            return df

        except Exception as e:
            print(f"Query error: {e}")
            return pd.DataFrame()

    # -------------------------------------------------------------
    # TEMPERATURE QUERIES
    
    # TODO -- double check that this exists
    def get_indoor_temperature(self, start_time='-7d', aggregate_window='1h'):
        """Get indoor temperature from thermostat in Celsius."""
        query = f"""
        from(bucket: "dchouse")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "temperature_thermostat"
                and r._field == "value" and r.location == "thermostat")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "indoor_temp")
        """
        return self.query(query)

    # TODO -- CONNECT WEATHER API FOR OUTDOOR DATA
    def get_outdoor_temperature(self, start_time='-7d', aggregate_window='1h'):
        """Get outdoor temperature from weather data."""
        query = f"""
        from(bucket: "dchouse")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "temperature_outdoor"
                and r._field == "value")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "outdoor_temp")
        """
        return self.query(query)

    def get_indoor_humidity(self, start_time='-7d', aggregate_window='1h'):
        """Get indoor humidity."""
        query = f"""
        from(bucket: "dchouse")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "relative_humidity"
                and r._field == "value")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "indoor_humidity")
        """
        # is it relative_humidity or humidity_thermostat?
        return self.query(query)

    # -------------------------------------------------------------
    # ENERGY QUERIES

    def get_grid_power(self, start_time='-7d', aggregate_window='1h'):
        """Get total grid power consumption from total_home_demand measurement."""
        query = f"""
        from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "total_home_demand")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "total_power")
        """
        return self.query(query)

    def get_energy_usage_by_device(self, start_time='-30d', aggregate_window='1h'):
        """Get energy usage broken down by device."""
        query = f"""
        from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement != "MainA_L" and r._measurement != "MainA_R")
            |> filter(fn: (r) => r._measurement != "MainB_L" and r._measurement != "MainB_R")
            |> filter(fn: (r) => r._measurement != "MainN_L" and r._measurement != "MainN_R")
            |> filter(fn: (r) => r._measurement != "grid_l" and r._measurement != "grid_lP")
            |> filter(fn: (r) => r._measurement != "grid_r" and r._measurement != "grid_rP")
            |> filter(fn: (r) => r._measurement != "ampsB_R" and r._measurement != "ampsB_L")
            |> filter(fn: (r) => r._measurement != "ampsA_R" and r._measurement != "ampsA_L")
            |> filter(fn: (r) => r._measurement != "ampsN_R" and r._measurement != "ampsN_L")
            |> filter(fn: (r) => r._measurement != "AMPS_AHU1" and r._measurement != "AMPS_AHU2")
            |> filter(fn: (r) => r._measurement != "Volt_inR")
            |> filter(fn: (r) => r._measurement != "amps_HP")
            |> filter(fn: (r) => r._measurement != "HVAC_net")
            |> filter(fn: (r) => r._measurement != "ampstot_R" and r._measurement != "ampstot_L")
            |> filter(fn: (r) => r._measurement != "AHU_PF" and r._measurement != "AUX_PF")
            |> filter(fn: (r) => r._measurement != "AC_unitout_PF")
            |> filter(fn: (r) => r._measurement != "amps_HPWH")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
        """
        return self.query(query)

    def get_actual_energy_consumption(self, start_time='-30d'):
        """Get actual energy consumption in kWh from total_home_demand measurement."""
        query = f"""
        from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "total_home_demand")
            |> aggregateWindow(every: 1h, fn: mean)
            |> sum()
            |> yield(name: "Total")
        """
        df = self.query(query)

        # Convert to kWh
        if not df.empty and '_value' in df.columns:
            total_wh = df['_value'].sum()
            total_kwh = total_wh / 1000
            return total_kwh

        return 0

    def get_predicted_energy_bill(self, start_time='-30d'):
        """Calculate predicted energy bill based on recent usage."""
        actual_kwh = self.get_actual_energy_consumption(start_time)
        cost = actual_kwh * 0.15
        return pd.DataFrame({'value': [cost], 'unit': ['USD']})

    # -------------------------------------------------------------
    # HEAT PUMP QUERIES

    def get_heat_pump_temperature(self, start_time='-7d', aggregate_window='1h'):
        """Get heat pump temperature readings."""
        query = f"""
        from(bucket: "dchouse")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "temperature"
                and r._field == "value"
                and r.location == "heat_pump")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "hp_temp")
        """
        return self.query(query)

    def get_heat_pump_power(self, start_time='-30d', aggregate_window='1h'):
        """Get HVAC power consumption (outdoor HVAC + AHU_main + AHU_aux)."""
        query = f"""
        outdoor = from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "AC_unitout")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)

        ahu_main = from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "AHU_main")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)

        ahu_aux = from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "AHU_Aux")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)

        union(tables: [outdoor, ahu_main, ahu_aux])
            |> group(columns: ["_time"])
            |> sum(column: "_value")
            |> yield(name: "hvac_total")
        """
        return self.query(query)

    def get_hp_water_heater_temperature(self, start_time='-7d', aggregate_window='1h'):
        """Get heat pump water heater temperature readings."""
        query = f"""
        from(bucket: "dchouse")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "temperature"
                and r._field == "value"
                and r.location == "water_heater")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "hpwh_temp")
        """
        return self.query(query)

    def get_hp_water_heater_power(self, start_time='-30d', aggregate_window='1h'):
        """Get heat pump water heater power consumption."""
        query = f"""
        from(bucket: "electrical")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "HPWH")
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> yield(name: "hpwh_power")
        """
        return self.query(query)

    # -------------------------------------------------------------
    # MPC PERFORMANCE QUERIES

    def get_mpc_data(self, start_time='-30d', aggregate_window='6m'):
        """Get MPC thermostat data for energy savings calculations."""
        query = f"""
        MPCdata = from(bucket: "dchouse")
            |> range(start: {start_time})
            |> filter(fn: (r) => r._measurement == "temperature_thermostat"
                and r._field == "value" and r.location == "thermostat")
            |> sort(columns: ["_time"], desc: true)
            |> aggregateWindow(every: {aggregate_window}, fn: mean)
            |> filter(fn: (r) => exists r._value)
            |> yield(name: "thermostat")
        """
        return self.query(query)

    # close db connection
    def close(self):
        self.client.close()
