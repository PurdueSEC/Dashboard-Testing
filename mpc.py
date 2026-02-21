# MPC Energy Savings Calculations
import pandas as pd
import numpy as np


# Heating and cooling constants
RBC_C1_HEATING = 0.1958333333
C2_HEATING = -8
MPC_C1_HEATING = 0.1595833333

RBC_C1_COOLING = 0.1266666667
C2_COOLING = 6.4
MPC_C1_COOLING = 0.1091666667


class MPCCalculator:
    # MPC energy savings

    def __init__(self):
        self.rbc_c1_heating = RBC_C1_HEATING
        self.c2_heating = C2_HEATING
        self.mpc_c1_heating = MPC_C1_HEATING
        self.rbc_c1_cooling = RBC_C1_COOLING
        self.c2_cooling = C2_COOLING
        self.mpc_c1_cooling = MPC_C1_COOLING

    def calculate_energy_consumption(self, temperature_df, outdoor_temp_df,
                                    mode='heating', control_type='mpc'):
        """
        Calculate energy consumption based on temperature data.

        Parameters:
        -----------
        temperature_df : pandas DataFrame
            Indoor temperature data with '_time' and '_value' columns
        outdoor_temp_df : pandas DataFrame
            Outdoor temperature data with '_time' and '_value' columns
        mode : str
            'heating' or 'cooling'
        control_type : str
            'mpc' or 'rbc'

        Returns:
        --------
        pandas DataFrame with calculated energy consumption
        """
        # Merge indoor and outdoor temperature data
        merged = pd.merge(temperature_df, outdoor_temp_df,
                         on='_time', suffixes=('_indoor', '_outdoor'))

        # select heating/cooling constants based on what is passed in
        if mode == 'heating':
            c1 = self.mpc_c1_heating if control_type == 'mpc' else self.rbc_c1_heating
            c2 = self.c2_heating
        else:  # cooling
            c1 = self.mpc_c1_cooling if control_type == 'mpc' else self.rbc_c1_cooling
            c2 = self.c2_cooling

        # (energy consumption) E = C1 * (T_indoor - T_outdoor) + C2
        merged['energy'] = c1 * (merged['_value_indoor'] - merged['_value_outdoor']) + c2

        # get rid of erroneous negative values
        merged['energy'] = merged['energy'].clip(lower=0)

        return merged[['_time', 'energy']]

    def calculate_total_energy_savings(self, mpc_energy_df, rbc_energy_df):
        """
        Calculate total energy savings between MPC and RBC.

        Parameters:
        -----------
        mpc_energy_df : pandas DataFrame
            MPC energy consumption data
        rbc_energy_df : pandas DataFrame
            RBC energy consumption data

        Returns:
        --------
        float : Total energy savings in kWh
        """
        mpc_total = mpc_energy_df['energy'].sum()
        rbc_total = rbc_energy_df['energy'].sum()

        # savings in Wh, convert to kWh
        savings_wh = rbc_total - mpc_total
        savings_kwh = savings_wh / 1000

        return savings_kwh

    def calculate_cost_savings(self, energy_savings_kwh, electricity_rate=0.15):
        """
        Calculate cost savings from energy savings.

        Parameters:
        -----------
        energy_savings_kwh : float
            Energy savings in kWh
        electricity_rate : float
            Electricity cost per kWh in USD (default $0.15)

        Returns:
        --------
        float : Cost savings in USD
        """
        return energy_savings_kwh * electricity_rate

    def calculate_co2_savings(self, energy_savings_kwh, co2_per_kwh=0.92):
        """
        Calculate CO2 emissions savings.

        Parameters:
        -----------
        energy_savings_kwh : float
            Energy savings in kWh
        co2_per_kwh : float
            CO2 emissions per kWh in pounds (default 0.92 lbs)

        Returns:
        --------
        float : CO2 savings in pounds
        """
        return energy_savings_kwh * co2_per_kwh

    def calculate_equivalent_miles_driven(self, co2_savings_lbs, lbs_per_mile=0.79):
        """
        Calculate equivalent miles driven based on CO2 savings.

        Parameters:
        -----------
        co2_savings_lbs : float
            CO2 savings in pounds
        lbs_per_mile : float
            CO2 emissions per mile driven (default 0.79 lbs for average car)

        Returns:
        --------
        float : Equivalent miles driven
        """
        return co2_savings_lbs / lbs_per_mile

    def calculate_all_savings_metrics(self, temperature_df, outdoor_temp_df,
                                     mode='heating', electricity_rate=0.15):
        """
        Calculate all savings metrics (energy, cost, CO2, miles).

        Parameters:
        -----------
        temperature_df : pandas DataFrame
            Indoor temperature data
        outdoor_temp_df : pandas DataFrame
            Outdoor temperature data
        mode : str
            'heating' or 'cooling'
        electricity_rate : float
            Electricity cost per kWh

        Returns:
        --------
        dict with all savings metrics
        """
        # Calculate energy consumption for both MPC and RBC
        mpc_energy = self.calculate_energy_consumption(
            temperature_df, outdoor_temp_df, mode=mode, control_type='mpc')
        rbc_energy = self.calculate_energy_consumption(
            temperature_df, outdoor_temp_df, mode=mode, control_type='rbc')

        # Calculate savings
        energy_savings_kwh = self.calculate_total_energy_savings(mpc_energy, rbc_energy)
        cost_savings_usd = self.calculate_cost_savings(energy_savings_kwh, electricity_rate)
        co2_savings_lbs = self.calculate_co2_savings(energy_savings_kwh)
        miles_driven = self.calculate_equivalent_miles_driven(co2_savings_lbs)

        return {
            'energy_savings_kwh': energy_savings_kwh,
            'cost_savings_usd': cost_savings_usd,
            'co2_savings_lbs': co2_savings_lbs,
            'equivalent_miles': miles_driven,
            'mpc_energy': mpc_energy,
            'rbc_energy': rbc_energy
        }

    def create_mpc_comparison_df(self, mpc_energy_df, rbc_energy_df):
        """
        Create a DataFrame comparing MPC and RBC energy consumption over time.

        Parameters:
        -----------
        mpc_energy_df : pandas DataFrame
            MPC energy consumption data
        rbc_energy_df : pandas DataFrame
            RBC energy consumption data

        Returns:
        --------
        pandas DataFrame with both MPC and RBC data
        """
        merged = pd.merge(mpc_energy_df, rbc_energy_df,
                         on='_time', suffixes=('_mpc', '_rbc'))
        return merged

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
