import pandas as pd
from datetime import timedelta
import os
import re

# Function to list available directories in the current working directory, excluding hidden ones
def list_available_directories(path):
    return [d for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d)) and not d.startswith('.')]

# Function to sort directories based on their dates
def sort_directories_by_date(directories):
    def parse_directory_date(directory_name):
        if re.match(r'^\d{6}$', directory_name):  # Single day format
            return pd.to_datetime(directory_name, format='%y%m%d')
        elif re.match(r'^\d{6}-\d{6}$', directory_name):  # Period format
            start_date = pd.to_datetime(directory_name.split('-')[0], format='%y%m%d')
            return start_date
        else:
            raise ValueError("Directory name does not match expected formats")

    return sorted(directories, key=parse_directory_date)

# Function to check if a directory is for a single day or a period
def determine_directory_type(directory_name):
    if re.match(r'^\d{6}$', directory_name):
        return 'single_day'
    elif re.match(r'^\d{6}-\d{6}$', directory_name):
        return 'period'
    else:
        raise ValueError("Directory name does not match expected formats")

# Function to format time as HH:MM
def format_time(duration):
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}"

# Function to print a block of text inside a box
def print_in_box(text):
    lines = text.strip().split('\n')
    max_length = max(len(line) for line in lines)
    print('+' + '-' * (max_length + 2) + '+')
    for line in lines:
        print('| ' + line.ljust(max_length) + ' |')
    print('+' + '-' * (max_length + 2) + '+')

# Current working directory
base_directory = os.getcwd()

# List and sort available directories by date
available_directories = sort_directories_by_date(list_available_directories(base_directory))

x = 5   # change time_threshold here

while x > 0:
    print("time_threshold: " + str(x))
        
    # Process each directory
    for selected_directory in available_directories:

        # Determine if the selected directory is a single day or a period
        directory_type = determine_directory_type(selected_directory)

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
        time_threshold = timedelta(minutes=x)  # Minimum cumulative duration of drop or rise to change state

        # Process each room's data
        for room, file_path in file_paths.items():
            # Load the CSV data from a file
            if not os.path.exists(file_path):
                print_in_box(f"File not found for {room} in {selected_directory}. Skipping...")
                continue

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
                time_diff = df.at[i, 'Timestamp'] - df.at[i-1, 'Timestamp']  # Corrected line

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

        # Calculate totals and averages
        total_ac_running_time = sum(ac_running_time.values(), timedelta(0))
        total_ac_running_hours = sum(ac_running_hours.values())
        total_kwh_consumed = total_ac_running_hours * power_consumption_rate

        # Create the output block
        output_block = f"{'Room':<12} {'Time Running':<18} {'Energy Consumed':<22}\n"
        output_block += f"{'----':<12} {'----------------':<18} {'-------------------':<22}\n"
        for room in ac_running_hours:
            if ac_running_hours[room] > 0:
                formatted_running_time = format_time(ac_running_time[room])
                total_kwh = ac_running_hours[room] * power_consumption_rate
                output_block += f"{room:<12} {formatted_running_time:<18} {total_kwh:.2f} kWh\n"
        output_block += f"{'----':<12} {'----------------':<18} {'-------------------':<22}\n"
        output_block += f"{'Total':<12} {format_time(total_ac_running_time):<18} {total_kwh_consumed:.2f} kWh\n"

        # Additional information block
        if directory_type == 'single_day':
            output_block += f"\nDate: {time_period['Wohnzimmer'][0]}"
        elif directory_type == 'period':
            # Calculate the number of days in the period
            num_days = (time_period['Wohnzimmer'][1] - time_period['Wohnzimmer'][0]).days + 1

            # Calculate average running time and consumption per day
            avg_running_time_per_day = total_ac_running_time / num_days
            avg_consumption_per_day = total_ac_running_hours / num_days

            # Format average running time
            formatted_avg_running_time = format_time(avg_running_time_per_day)

            # Add to additional info
            output_block += f"\n{'Average/Day':<12} {formatted_avg_running_time:<18} {avg_consumption_per_day * power_consumption_rate:.2f} kWh\n"
            output_block += f"\nNumber of days in the period: {num_days}\n"
            output_block += f"Time period covered by data: {time_period['Wohnzimmer'][0]} to {time_period['Wohnzimmer'][1]}"

        # Print all information inside a single box
        print_in_box(output_block)

    x -= 0.5
