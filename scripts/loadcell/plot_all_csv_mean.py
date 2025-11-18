import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import os
import numpy as np

def plot_all_csv_with_mean(data_dir="data_1"):
    """Plot all CSV files with transparent lines and highlight the mean curve"""
    
    # Find all CSV files in the specified directory
    if not os.path.exists(data_dir):
        print(f"Directory '{data_dir}' not found. Trying current directory...")
        data_dir = "."
    
    csv_pattern = os.path.join(data_dir, "loadcell_data_*.csv")
    csv_files = glob.glob(csv_pattern)
    if not csv_files:
        print(f"No CSV files found in '{data_dir}' directory.")
        return
    
    csv_files.sort(key=os.path.getmtime)  # Sort by modification time
    print(f"Found {len(csv_files)} CSV files")
    
    # Load all CSV files and align them by peak force
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
                # Fallback: use row index as time
                df['elapsed_time'] = df.index * 0.1
            
            # Filter out invalid data points
            # Remove rows where both force and pressure are zero (initialization data)
            # Also filter out invalid pressure values (< 1V is likely invalid for this sensor)
            valid_mask = ((df['force_N'] != 0) | (df['pressure_v'] != 0)) & (df['pressure_v'] >= 1.0)
            df_clean = df[valid_mask].copy()
            
            # If filtering removed too much, be less strict
            if len(df_clean) < len(df) * 0.5:  # If we removed more than 50%
                # Only filter zeros, keep all pressure values
                valid_mask = (df['force_N'] != 0) | (df['pressure_v'] != 0)
                df_clean = df[valid_mask].copy()
            
            if len(df_clean) == 0:
                df_clean = df.copy()
            
            if len(df_clean) > 0:
                all_data.append(df_clean)
                print(f"  Loaded {len(df_clean)} points from {os.path.basename(csv_file)}")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            continue
    
    if not all_data:
        print("No valid data found in CSV files.")
        return
    
    # Align all datasets by peak force
    print("\nAligning datasets by peak force...")
    for df in all_data:
        # Find peak force (maximum absolute value)
        force_abs = np.abs(df['force_N'].values)
        peak_idx = np.argmax(force_abs)
        peak_time = df['elapsed_time'].iloc[peak_idx]
        peak_force = df['force_N'].iloc[peak_idx]
        
        # Shift time so peak occurs at time = 0
        df_aligned = df.copy()
        df_aligned['elapsed_time'] = df_aligned['elapsed_time'] - peak_time
        
        aligned_data.append(df_aligned)
        print(f"  Peak force: {peak_force:.5f} N at t={peak_time:.2f}s -> aligned to t=0")
    
    # Determine time range for interpolation (use range that covers most data)
    # Find min and max times across all aligned datasets
    all_times = []
    for df in aligned_data:
        all_times.extend(df['elapsed_time'].values)
    
    min_time = min(all_times)
    max_time = max(all_times)
    
    # Create a common time grid (use a reasonable range around the peak)
    # Use the range that covers most datasets (e.g., -5 to +10 seconds from peak)
    time_before = abs(min_time) if min_time < 0 else 5  # At least 5s before peak
    time_after = max_time if max_time > 0 else 10  # At least 10s after peak
    
    # Create reference time grid centered at peak (t=0)
    reference_time = np.linspace(-time_before, time_after, 500)  # 500 points for smooth interpolation
    
    # Interpolate force and pressure for each aligned dataset
    interpolated_forces = []
    interpolated_pressures = []
    
    for df in aligned_data:
        # Interpolate to reference time points
        # Only interpolate within the actual data range
        df_times = df['elapsed_time'].values
        df_forces = df['force_N'].values
        df_pressures = df['pressure_v'].values
        
        # Filter out invalid pressure values before interpolation
        # Pressure should be in reasonable range (1-5V for this sensor)
        valid_pressure_mask = (df_pressures >= 1.0) & (df_pressures <= 5.0)
        
        # If we have valid pressure data, use it; otherwise use all data
        if np.any(valid_pressure_mask):
            # Interpolate force (use all data)
            force_interp = np.interp(reference_time, df_times, df_forces, 
                                     left=np.nan, right=np.nan)
            
            # Interpolate pressure (only use valid pressure points)
            valid_times = df_times[valid_pressure_mask]
            valid_pressures = df_pressures[valid_pressure_mask]
            
            # Only interpolate where we have valid data
            pressure_interp = np.interp(reference_time, valid_times, valid_pressures,
                                       left=np.nan, right=np.nan)
        else:
            # Fallback: use all data if no valid pressure found
            force_interp = np.interp(reference_time, df_times, df_forces, 
                                     left=np.nan, right=np.nan)
            pressure_interp = np.interp(reference_time, df_times, df_pressures,
                                       left=np.nan, right=np.nan)
        
        interpolated_forces.append(force_interp)
        interpolated_pressures.append(pressure_interp)
    
    # Calculate mean curves (ignoring NaN values)
    # Convert to numpy array for easier handling
    forces_array = np.array(interpolated_forces)
    pressures_array = np.array(interpolated_pressures)
    
    # Calculate mean ignoring NaN (only where we have data from at least one file)
    mean_force = np.nanmean(forces_array, axis=0)
    mean_pressure = np.nanmean(pressures_array, axis=0)
    
    # Calculate std for error bands (ignoring NaN)
    std_force = np.nanstd(forces_array, axis=0)
    std_pressure = np.nanstd(pressures_array, axis=0)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle(f'All Load Cell Data - Mean Curve Highlighted ({len(all_data)} files)', 
                 fontsize=14, fontweight='bold')
    
    # Plot Force
    # Plot all individual aligned curves with transparency
    for i, df in enumerate(aligned_data):
        ax1.plot(df['elapsed_time'], df['force_N'], 
                alpha=0.2, linewidth=0.8, color='blue', label='Individual runs' if i == 0 else '')
    
    # Plot mean curve (highlighted) - only where we have valid data
    valid_mask = ~np.isnan(mean_force)
    if np.any(valid_mask):
        ax1.plot(reference_time[valid_mask], mean_force[valid_mask], 'b-', linewidth=3, 
                label='Mean', color='darkblue', zorder=10)
        
        # Optional: Add std error bands
        ax1.fill_between(reference_time[valid_mask], 
                         mean_force[valid_mask] - std_force[valid_mask], 
                         mean_force[valid_mask] + std_force[valid_mask],
                         alpha=0.2, color='blue', label='±1 Std Dev')
    
    ax1.set_xlabel('Time relative to peak (s)')
    ax1.set_ylabel('Force (N)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Force Measurement - All Runs (Aligned by Peak)')
    ax1.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Peak alignment')
    ax1.legend(loc='upper left')
    
    # Plot Pressure
    # Plot all individual aligned curves with transparency
    for i, df in enumerate(aligned_data):
        ax2.plot(df['elapsed_time'], df['pressure_v'], 
                alpha=0.2, linewidth=0.8, color='red', label='Individual runs' if i == 0 else '')
    
    # Plot mean curve (highlighted) - only where we have valid data
    valid_mask_p = ~np.isnan(mean_pressure)
    if np.any(valid_mask_p):
        ax2.plot(reference_time[valid_mask_p], mean_pressure[valid_mask_p], 'r-', linewidth=3, 
                label='Mean', color='darkred', zorder=10)
        
        # Optional: Add std error bands
        ax2.fill_between(reference_time[valid_mask_p], 
                         mean_pressure[valid_mask_p] - std_pressure[valid_mask_p], 
                         mean_pressure[valid_mask_p] + std_pressure[valid_mask_p],
                         alpha=0.2, color='red', label='±1 Std Dev')
    
    ax2.set_xlabel('Time relative to peak (s)')
    ax2.set_ylabel('Pressure (V)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Air Pressure Measurement - All Runs (Aligned by Peak Force)')
    ax2.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Peak alignment')
    ax2.legend(loc='upper left')
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total files: {len(all_data)}")
    print(f"Total data points (mean): {len(reference_time)}")
    print(f"\nForce (N) - Mean across all runs:")
    print(f"  Min: {mean_force.min():.5f}")
    print(f"  Max: {mean_force.max():.5f}")
    print(f"  Mean: {mean_force.mean():.5f}")
    print(f"  Std: {mean_force.std():.5f}")
    print(f"\nPressure (V) - Mean across all runs:")
    print(f"  Min: {mean_pressure.min():.4f}")
    print(f"  Max: {mean_pressure.max():.4f}")
    print(f"  Mean: {mean_pressure.mean():.4f}")
    print(f"  Std: {mean_pressure.std():.4f}")

def main():
    """Main function"""
    print("Load Cell Data - All CSV Plotter with Mean Curve")
    print("=" * 60)
    plot_all_csv_with_mean()

if __name__ == "__main__":
    main()

