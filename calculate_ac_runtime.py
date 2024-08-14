import pandas as pd
from datetime import timedelta

# Define file paths for both CSV files
file_paths = {
    'Wohnzimmer': 'Wohnzimmer_data.csv',
    'Schlafzimmer': 'Schlafzimmer_data.csv'
}

# Initialize dictionaries to hold the total AC running time, hours, and time period for each room
ac_running_time = {'Wohnzimmer': timedelta(0), 'Schlafzimmer': timedelta(0)}
ac_running_hours = {'Wohnzimmer': 0.0, 'Schlafzimmer': 0.0}
time_period = {'Wohnzimmer': (None, None), 'Schlafzimmer': (None, None)}

# Power consumption rate in kWh per hour
power_consumption_rate = 1.3

# Process each room's data
for room, file_path in file_paths.items():
    # Load the CSV data from a file
    df = pd.read_csv(file_path)

    # Convert Timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Calculate the temperature difference between consecutive minutes
    df['Temp_Diff'] = df['Temperature_Celsius(°C)'].diff()

    # Initialize a flag to track whether the AC is running
    df['AC_Running'] = False

    # Identify periods where the temperature drops more than 0.1°C per minute
    threshold = -0.1
    ac_start_index = None

    for i in range(1, len(df)):
        # Check if the temperature is dropping at a high rate
        if df.at[i, 'Temp_Diff'] < threshold:
            if ac_start_index is None:
                ac_start_index = i  # AC starts running
        else:
            # If the temperature starts rising again and the AC was previously running
            if ac_start_index is not None:
                # Calculate the duration the AC was running
                ac_running_time[room] += df.at[i, 'Timestamp'] - df.at[ac_start_index, 'Timestamp']
                ac_start_index = None  # Reset the start index

    # If the temperature drop continues until the end of the data, count that period as well
    if ac_start_index is not None:
        ac_running_time[room] += df.at[len(df) - 1, 'Timestamp'] - df.at[ac_start_index, 'Timestamp']

    # Calculate the total running time in hours for the room
    ac_running_hours[room] = ac_running_time[room].total_seconds() / 3600.0

    # Store the time period covered by the data
    time_period[room] = (df['Timestamp'].min().date(), df['Timestamp'].max().date())

# Calculate and print results for each room
for room in ac_running_hours:
    total_kwh_consumed = ac_running_hours[room] * power_consumption_rate

    # Format total running time as hours and minutes
    hours, remainder = divmod(ac_running_time[room].total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    formatted_running_time = f"{int(hours):02}:{int(minutes):02}"

    # Format time period
    start_date, end_date = time_period[room]
    period_formatted = f"{start_date} to {end_date}"

    print(f"Total time AC was running in {room}: {formatted_running_time}")
    print(f"Total energy consumed by AC in {room}: {total_kwh_consumed:.2f} kWh")
    print(f"Time period covered by {room} data: {period_formatted}\n")

# Calculate and print results for both rooms combined
total_running_hours_combined = sum(ac_running_hours.values())
total_kwh_consumed_combined = total_running_hours_combined * power_consumption_rate

# Format total running time for both rooms combined
total_hours, remainder = divmod(total_running_hours_combined * 3600, 3600)
total_minutes, _ = divmod(remainder, 60)
formatted_total_running_time = f"{int(total_hours):02}:{int(total_minutes):02}"

# Determine the overall time period covered by both rooms
overall_start_date = min(time_period['Wohnzimmer'][0], time_period['Schlafzimmer'][0])
overall_end_date = max(time_period['Wohnzimmer'][1], time_period['Schlafzimmer'][1])
overall_period_formatted = f"{overall_start_date} to {overall_end_date}"

print(f"Total time AC was running in both rooms: {formatted_total_running_time}")
print(f"Total energy consumed by AC in both rooms: {total_kwh_consumed_combined:.2f} kWh")
print(f"Time period covered by both rooms data: {overall_period_formatted}")
