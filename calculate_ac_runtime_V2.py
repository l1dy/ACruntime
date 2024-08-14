import pandas as pd
from datetime import timedelta
import os

# Function to list available directories in the current working directory, excluding hidden ones
def list_available_directories(path):
    return [d for d in os.listdir(path) 
            if os.path.isdir(os.path.join(path, d)) and not d.startswith('.')]

# Function to prompt user for a directory selection
def prompt_user_selection(options, prompt_message):
    print(prompt_message)
    for idx, option in enumerate(options):
        print(f"{idx}: {option}")
    selected_index = int(input("Enter the index of the selected option: "))
    return options[selected_index]

# Current working directory
base_directory = os.getcwd()

# List available directories excluding hidden ones
available_directories = list_available_directories(base_directory)

# Prompt user for directory selection
selected_directory = prompt_user_selection(available_directories, "Select the directory for the data:")

# Define file paths for both CSV files in the selected directory
directory_path = os.path.join(base_directory, selected_directory)
file_paths = {
    'Wohnzimmer': os.path.join(directory_path, 'Wohnzimmer_data.csv'),
    'Schlafzimmer': os.path.join(directory_path, 'Schlafzimmer_data.csv')
}

# Initialize dictionaries to hold the total AC running time, hours, and time period for each room
ac_running_time = {'Wohnzimmer': timedelta(0), 'Schlafzimmer': timedelta(0)}
ac_running_hours = {'Wohnzimmer': 0.0, 'Schlafzimmer': 0.0}
time_period = {'Wohnzimmer': (None, None), 'Schlafzimmer': (None, None)}

# Power consumption rate in kWh per hour
power_consumption_rate = 1.3

# Thresholds
temp_drop_threshold = -0.1  # Temperature drop per minute to consider AC running
temp_rise_threshold = 0.1   # Temperature rise per minute to consider AC stopped
time_threshold = timedelta(minutes=5)  # Minimum cumulative duration of drop or rise to change state

# Process each room's data
for room, file_path in file_paths.items():
    # Load the CSV data from a file
    df = pd.read_csv(file_path)

    # Convert Timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Calculate the temperature difference between consecutive minutes
    df['Temp_Diff'] = df['Temperature_Celsius(°C)'].diff()

    # Initialize variables to track AC state
    ac_running = False
    ac_start_time = None
    drop_duration = timedelta(0)
    rise_duration = timedelta(0)

    for i in range(1, len(df)):
        time_diff = df.at[i, 'Timestamp'] - df.at[i-1, 'Timestamp']

        if df.at[i, 'Temp_Diff'] < temp_drop_threshold:  # Temperature dropping
            drop_duration += time_diff
            rise_duration = timedelta(0)  # Reset rise duration

            if drop_duration >= time_threshold and not ac_running:
                ac_start_time = df.at[i, 'Timestamp']
                ac_running = True

        elif df.at[i, 'Temp_Diff'] > temp_rise_threshold:  # Temperature rising
            rise_duration += time_diff
            drop_duration = timedelta(0)  # Reset drop duration

            if rise_duration >= time_threshold and ac_running:
                ac_running_time[room] += df.at[i, 'Timestamp'] - ac_start_time
                ac_running = False

        else:
            # If temperature change is within thresholds, keep durations but do not change states
            continue

    # If the AC was still running at the end of the data, count that period as well
    if ac_running:
        ac_running_time[room] += df['Timestamp'].iloc[-1] - ac_start_time

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
