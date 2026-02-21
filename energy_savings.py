# Energy Consumption Calculations using Month-Based Model
import pandas as pd
import numpy as np


# Month-based energy consumption rates (kWh/hr)
BASE_RATE_ELECTRIC = 2.08  # Pure electric usage (all months)
BASE_RATE_GAS = 0.34       # Non-heating gas usage (all months)
BASE_RATE = BASE_RATE_ELECTRIC + BASE_RATE_GAS  # Total: 2.42 kWh/hr

# Additional heating gas usage for winter months (Nov-Mar)
HEATING_RATES = {
    11: 2.43,  # November
    12: 4.75,  # December
    1: 6.67,   # January
    2: 6.76,   # February
    3: 4.96    # March
}

# Energy cost rates
ELECTRIC_RATE = 0.15    # $/kWh for electricity
GAS_RATE = 0.0226       # $/kWh for gas


class EnergyCalculator:
    """Energy consumption calculator using month-based model."""

    def __init__(self):
        self.base_rate = BASE_RATE
        self.base_rate_electric = BASE_RATE_ELECTRIC
        self.base_rate_gas = BASE_RATE_GAS
        self.heating_rates = HEATING_RATES
        self.electric_rate = ELECTRIC_RATE
        self.gas_rate = GAS_RATE

    def calculate_energy_consumption(self, temperature_df, outdoor_temp_df):
        """
        Calculate energy consumption based on month using fixed hourly rates.

        Model:
        - Base rate (all months): 2.42 kWh/hr (electricity + non-heating gas)
        - Additional heating gas (Nov-Mar):
          - November: +2.43 kWh/hr
          - December: +4.75 kWh/hr
          - January: +6.67 kWh/hr
          - February: +6.76 kWh/hr
          - March: +4.96 kWh/hr

        Parameters:
        -----------
        temperature_df : pandas DataFrame
            Indoor temperature data with '_time' and '_value' columns
            (temperature values not used, only timestamps)
        outdoor_temp_df : pandas DataFrame
            Outdoor temperature data (not used, kept for compatibility)

        Returns:
        --------
        pandas DataFrame with calculated energy consumption in kWh
        """
        # Use indoor temperature df for timestamps
        df = temperature_df.copy()

        # Convert _time to datetime if it's not already
        df['_time'] = pd.to_datetime(df['_time'])

        # Extract month from timestamp
        df['month'] = df['_time'].dt.month

        # Calculate hourly energy rate based on month
        df['energy'] = df['month'].apply(lambda m:
            self.base_rate + self.heating_rates.get(m, 0)
        )

        return df[['_time', 'energy']]

    def calculate_total_energy(self, energy_df):
        """
        Calculate total energy consumption.

        Parameters:
        -----------
        energy_df : pandas DataFrame
            Energy consumption data

        Returns:
        --------
        float : Total energy in kWh
        """
        return energy_df['energy'].sum()

    def calculate_cost(self, energy_kwh, electricity_rate=0.15):
        """
        Calculate cost from energy consumption.

        Parameters:
        -----------
        energy_kwh : float
            Energy in kWh
        electricity_rate : float
            Electricity cost per kWh in USD (default $0.15)

        Returns:
        --------
        float : Cost in USD
        """
        return energy_kwh * electricity_rate

    def calculate_co2_emissions(self, energy_kwh, co2_per_kwh=0.417):
        """
        Calculate CO2 emissions.

        Parameters:
        -----------
        energy_kwh : float
            Energy in kWh
        co2_per_kwh : float
            CO2 emissions per kWh in kilograms (default 0.417 kg)

        Returns:
        --------
        float : CO2 emissions in kilograms
        """
        return energy_kwh * co2_per_kwh

    def calculate_equivalent_km_driven(self, co2_kg, kg_per_km=0.222):
        """
        Calculate equivalent kilometers driven based on CO2 emissions.

        Parameters:
        -----------
        co2_kg : float
            CO2 emissions in kilograms
        kg_per_km : float
            CO2 emissions per kilometer driven (default 0.222 kg for average car)

        Returns:
        --------
        float : Equivalent kilometers driven
        """
        return co2_kg / kg_per_km

    def calculate_all_metrics(self, temperature_df, outdoor_temp_df, electricity_rate=0.15):
        """
        Calculate all energy metrics (energy, cost, CO2, miles).

        Parameters:
        -----------
        temperature_df : pandas DataFrame
            Indoor temperature data
        outdoor_temp_df : pandas DataFrame
            Outdoor temperature data
        electricity_rate : float
            Electricity cost per kWh (not used for model, kept for compatibility)

        Returns:
        --------
        dict with all energy metrics
        """
        # Calculate energy consumption
        energy_df = self.calculate_energy_consumption(temperature_df, outdoor_temp_df)

        # Calculate metrics
        total_energy_kwh = self.calculate_total_energy(energy_df)

        # Calculate cost with proper electric/gas breakdown
        # Electric cost: BASE_RATE_ELECTRIC (2.08 kWh/hr) at ELECTRIC_RATE ($0.15/kWh)
        # Gas cost: (BASE_RATE_GAS + heating_rate) at GAS_RATE ($0.0226/kWh)
        df = energy_df.copy()
        df['_time'] = pd.to_datetime(df['_time'])
        df['month'] = df['_time'].dt.month

        # Electric cost: always 2.08 kWh/hr
        electric_energy_kwh = len(df) * self.base_rate_electric
        electric_cost = electric_energy_kwh * self.electric_rate

        # Gas cost: base gas + monthly heating
        df['gas_energy'] = df['month'].apply(lambda m:
            self.base_rate_gas + self.heating_rates.get(m, 0)
        )
        gas_energy_kwh = df['gas_energy'].sum()
        gas_cost = gas_energy_kwh * self.gas_rate

        cost_usd = electric_cost + gas_cost

        co2_kg = self.calculate_co2_emissions(total_energy_kwh)
        km_driven = self.calculate_equivalent_km_driven(co2_kg)

        return {
            'total_energy_kwh': total_energy_kwh,
            'cost_usd': cost_usd,
            'co2_kg': co2_kg,
            'equivalent_km': km_driven,
            'energy_df': energy_df
        }


# TODO -- add weather API for outdoor temp then get rid of this function
def simulate_outdoor_temperature(start_date, end_date, base_temp=40,
                                amplitude=20, freq='1h'):
    """
    Simulate outdoor temperature data (for testing if no external data available).

    Parameters:
    -----------
    start_date : str or datetime
        Start date
    end_date : str or datetime
        End date
    base_temp : float
        Base temperature in Fahrenheit
    amplitude : float
        Temperature variation amplitude
    freq : str
        Frequency of data points

    Returns:
    --------
    pandas DataFrame with simulated outdoor temperature
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    # Simulate daily temperature variation
    hours = np.array([t.hour for t in date_range])
    temp_variation = amplitude * np.sin(2 * np.pi * (hours - 6) / 24)
    outdoor_temp = base_temp + temp_variation

    df = pd.DataFrame({
        '_time': date_range,
        '_value': outdoor_temp
    })

    return df
