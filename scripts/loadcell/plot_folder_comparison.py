import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import os
import numpy as np

def load_and_align_folder(folder_path, folder_name):
    """Load all CSV files from a folder and align them by peak force"""
    csv_pattern = os.path.join(folder_path, "loadcell_data_*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"No CSV files found in '{folder_path}'")
        return None
    
    csv_files.sort(key=os.path.getmtime)
    print(f"\n{folder_name}: Found {len(csv_files)} CSV files")
    
    all_data = []
    aligned_data = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # Parse timestamp and calculate elapsed time
            try:
                df['datetime'] = pd.to_datetime(df['timestamp'])
                start_time = df['datetime'].iloc[0]
                df['elapsed_time'] = (df['datetime'] - start_time).dt.total_seconds()
            except:
                df['elapsed_time'] = df.index * 0.1
            
            # Filter out invalid data points
            # Remove initialization zeros and invalid pressure values
            # Pressure should be in reasonable range (2-5V for this sensor, allowing some margin)
            valid_mask = ((df['force_N'] != 0) | (df['pressure_v'] != 0)) & (df['pressure_v'] >= 2.0) & (df['pressure_v'] <= 5.0)
            df_clean = df[valid_mask].copy()
            
            # If filtering removed too much, be less strict (only filter obvious zeros)
            if len(df_clean) < len(df) * 0.3:
                valid_mask = (df['force_N'] != 0) | (df['pressure_v'] != 0)
                df_clean = df[valid_mask].copy()
                # Still filter out pressure values that are clearly invalid
                valid_mask = (df_clean['pressure_v'] >= 1.5) | (df_clean['pressure_v'] == 0)
                df_clean = df_clean[valid_mask].copy()
            
            if len(df_clean) == 0:
                df_clean = df.copy()
            
            if len(df_clean) > 0:
                all_data.append(df_clean)
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            continue
    
    if not all_data:
        return None
    
    # Align all datasets by peak force
    print(f"  Aligning {len(all_data)} datasets by peak force...")
    for df in all_data:
        force_abs = np.abs(df['force_N'].values)
        peak_idx = np.argmax(force_abs)
        peak_time = df['elapsed_time'].iloc[peak_idx]
        
        df_aligned = df.copy()
        df_aligned['elapsed_time'] = df_aligned['elapsed_time'] - peak_time
        aligned_data.append(df_aligned)
    
    return aligned_data

def calculate_mean_curve(aligned_data, reference_time):
    """Calculate mean curve for aligned data"""
    if not aligned_data:
        return None, None, None, None
    
    interpolated_forces = []
    interpolated_pressures = []
    
    for df in aligned_data:
        df_times = df['elapsed_time'].values
        df_forces = df['force_N'].values
        df_pressures = df['pressure_v'].values
        
        # Filter valid pressure values (2-5V range, more strict)
        valid_pressure_mask = (df_pressures >= 2.0) & (df_pressures <= 5.0)
        
        # Interpolate force (use all data)
        force_interp = np.interp(reference_time, df_times, df_forces, 
                                 left=np.nan, right=np.nan)
        
        # Interpolate pressure (only use valid pressure points)
        if np.any(valid_pressure_mask):
            valid_times = df_times[valid_pressure_mask]
            valid_pressures = df_pressures[valid_pressure_mask]
            # Only interpolate where we have valid data
            pressure_interp = np.interp(reference_time, valid_times, valid_pressures,
                                       left=np.nan, right=np.nan)
        else:
            # If no valid pressure found, use all data but mark as potentially invalid
            pressure_interp = np.interp(reference_time, df_times, df_pressures,
                                       left=np.nan, right=np.nan)
            # Mark values outside reasonable range as NaN
            pressure_interp[(pressure_interp < 2.0) | (pressure_interp > 5.0)] = np.nan
        
        interpolated_forces.append(force_interp)
        interpolated_pressures.append(pressure_interp)
    
    # Calculate mean and std
    forces_array = np.array(interpolated_forces)
    pressures_array = np.array(interpolated_pressures)
    
    mean_force = np.nanmean(forces_array, axis=0)
    mean_pressure = np.nanmean(pressures_array, axis=0)
    std_force = np.nanstd(forces_array, axis=0)
    std_pressure = np.nanstd(pressures_array, axis=0)
    
    return mean_force, mean_pressure, std_force, std_pressure

def plot_folder_comparison(folders):
    """Compare data from multiple folders"""
    
    # Load and align data from each folder
    folder_data = {}
    all_times = []
    
    for folder_path, folder_name in folders:
        aligned_data = load_and_align_folder(folder_path, folder_name)
        if aligned_data:
            folder_data[folder_name] = aligned_data
            # Collect all time points
            for df in aligned_data:
                all_times.extend(df['elapsed_time'].values)
    
    if not folder_data:
        print("No valid data found in any folder.")
        return
    
    # Use fixed time window: ±5 seconds from peak
    reference_time = np.linspace(-5, 5, 500)
    
    # Calculate mean curves for each folder
    folder_means = {}
    colors = {'data_1': 'blue', 'data_2_max': 'green', 'data_3_min': 'red'}
    linestyles = {'data_1': '-', 'data_2_max': '--', 'data_3_min': '-.'}
    
    for folder_name, aligned_data in folder_data.items():
        mean_force, mean_pressure, std_force, std_pressure = calculate_mean_curve(
            aligned_data, reference_time)
        if mean_force is not None:
            folder_means[folder_name] = {
                'force': mean_force,
                'pressure': mean_pressure,
                'std_force': std_force,
                'std_pressure': std_pressure,
                'count': len(aligned_data)
            }
    
    # Create comparison plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('Load Cell Data Comparison - Multiple Folders', 
                 fontsize=16, fontweight='bold')
    
    # Plot Force comparison
    for folder_name, data in folder_means.items():
        color = colors.get(folder_name, 'gray')
        linestyle = linestyles.get(folder_name, '-')
        valid_mask = ~np.isnan(data['force'])
        
        if np.any(valid_mask):
            ax1.plot(reference_time[valid_mask], data['force'][valid_mask], 
                    linewidth=3, label=f'{folder_name} (n={data["count"]})', 
                    color=color, linestyle=linestyle, zorder=10)
            
            # Add std bands
            ax1.fill_between(reference_time[valid_mask],
                           data['force'][valid_mask] - data['std_force'][valid_mask],
                           data['force'][valid_mask] + data['std_force'][valid_mask],
                           alpha=0.15, color=color)
    
    ax1.set_xlabel('Time relative to peak (s)')
    ax1.set_ylabel('Force (N)', color='black')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Force Measurement Comparison (±5s from peak)')
    ax1.set_xlim(-5, 5)
    ax1.axvline(x=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax1.legend(loc='best')
    
    # Plot Pressure comparison
    for folder_name, data in folder_means.items():
        color = colors.get(folder_name, 'gray')
        linestyle = linestyles.get(folder_name, '-')
        valid_mask = ~np.isnan(data['pressure'])
        
        if np.any(valid_mask):
            ax2.plot(reference_time[valid_mask], data['pressure'][valid_mask], 
                    linewidth=3, label=f'{folder_name} (n={data["count"]})', 
                    color=color, linestyle=linestyle, zorder=10)
            
            # Add std bands
            ax2.fill_between(reference_time[valid_mask],
                           data['pressure'][valid_mask] - data['std_pressure'][valid_mask],
                           data['pressure'][valid_mask] + data['std_pressure'][valid_mask],
                           alpha=0.15, color=color)
    
    ax2.set_xlabel('Time relative to peak (s)')
    ax2.set_ylabel('Pressure (V)', color='black')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Air Pressure Measurement Comparison (±5s from peak)')
    ax2.set_xlim(-5, 5)
    ax2.axvline(x=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax2.legend(loc='best')
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    for folder_name, data in folder_means.items():
        print(f"\n{folder_name} (n={data['count']} runs):")
        print(f"  Force (N):")
        print(f"    Min: {np.nanmin(data['force']):.5f}")
        print(f"    Max: {np.nanmax(data['force']):.5f}")
        print(f"    Mean: {np.nanmean(data['force']):.5f}")
        print(f"    Std: {np.nanstd(data['force']):.5f}")
        print(f"  Pressure (V):")
        print(f"    Min: {np.nanmin(data['pressure']):.4f}")
        print(f"    Max: {np.nanmax(data['pressure']):.4f}")
        print(f"    Mean: {np.nanmean(data['pressure']):.4f}")
        print(f"    Std: {np.nanstd(data['pressure']):.4f}")

def main():
    """Main function"""
    print("Load Cell Data - Folder Comparison")
    print("=" * 60)
    
    # Define folders to compare
    folders = [
        ("data_1", "data_1"),
        ("data_2_max", "data_2_max"),
        ("data_3_min", "data_3_min")
    ]
    
    plot_folder_comparison(folders)

if __name__ == "__main__":
    main()

