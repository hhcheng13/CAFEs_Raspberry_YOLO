import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import os
import sys

def plot_csv_data(csv_file=None):
    """Read CSV file and plot force and pressure data"""
    
    # If no file specified, use the most recent CSV file
    if csv_file is None:
        csv_files = glob.glob("loadcell_data_*.csv")
        if not csv_files:
            print("No CSV files found in current directory.")
            return
        csv_file = max(csv_files, key=os.path.getmtime)
        print(f"Using most recent file: {csv_file}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"File not found: {csv_file}")
        return
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} data points from {csv_file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Parse timestamp
    try:
        df['datetime'] = pd.to_datetime(df['timestamp'])
        # Calculate elapsed time in seconds from first measurement
        start_time = df['datetime'].iloc[0]
        df['elapsed_time'] = (df['datetime'] - start_time).dt.total_seconds()
    except Exception as e:
        print(f"Error parsing timestamps: {e}")
        # Fallback: use row index as time
        df['elapsed_time'] = df.index * 0.1  # Assume ~10Hz sampling
    
    # Filter out zero/empty data points (initialization data)
    df_clean = df[(df['force_N'] != 0) | (df['pressure_v'] != 0)].copy()
    if len(df_clean) == 0:
        df_clean = df.copy()
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(f'Load Cell Data: {os.path.basename(csv_file)}', fontsize=14, fontweight='bold')
    
    # Plot Force
    ax1.plot(df_clean['elapsed_time'], df_clean['force_N'], 'b-', linewidth=1.5, label='Force')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Force (N)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Force Measurement')
    ax1.legend(loc='upper left')
    
    # Plot Pressure
    ax2.plot(df_clean['elapsed_time'], df_clean['pressure_v'], 'r-', linewidth=1.5, label='Air Pressure')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Pressure (V)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Air Pressure Measurement')
    ax2.legend(loc='upper left')
    
    # Add statistics text
    stats_text = f"Total points: {len(df_clean)}\n"
    stats_text += f"Force range: {df_clean['force_N'].min():.5f} - {df_clean['force_N'].max():.5f} N\n"
    stats_text += f"Pressure range: {df_clean['pressure_v'].min():.4f} - {df_clean['pressure_v'].max():.4f} V"
    fig.text(0.02, 0.02, stats_text, fontsize=9, verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total data points: {len(df_clean)}")
    print(f"\nForce (N):")
    print(f"  Min: {df_clean['force_N'].min():.5f}")
    print(f"  Max: {df_clean['force_N'].max():.5f}")
    print(f"  Mean: {df_clean['force_N'].mean():.5f}")
    print(f"  Std: {df_clean['force_N'].std():.5f}")
    print(f"\nPressure (V):")
    print(f"  Min: {df_clean['pressure_v'].min():.4f}")
    print(f"  Max: {df_clean['pressure_v'].max():.4f}")
    print(f"  Mean: {df_clean['pressure_v'].mean():.4f}")
    print(f"  Std: {df_clean['pressure_v'].std():.4f}")

def list_csv_files():
    """List all available CSV files"""
    csv_files = glob.glob("loadcell_data_*.csv")
    if not csv_files:
        print("No CSV files found in current directory.")
        return []
    
    csv_files.sort(key=os.path.getmtime, reverse=True)
    print("\nAvailable CSV files:")
    for i, f in enumerate(csv_files, 1):
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        size = os.path.getsize(f)
        print(f"  {i}. {f} ({mtime.strftime('%Y-%m-%d %H:%M:%S')}, {size} bytes)")
    return csv_files

def main():
    """Main function"""
    print("Load Cell CSV Data Plotter")
    print("=" * 50)
    
    # Check for command line argument
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        plot_csv_data(csv_file)
    else:
        # List available files
        csv_files = list_csv_files()
        
        if csv_files:
            # Plot the most recent file
            print(f"\nPlotting most recent file: {csv_files[0]}")
            plot_csv_data(csv_files[0])
        else:
            print("\nUsage: python plot_csv_data.py [csv_filename]")
            print("Or run without arguments to plot the most recent file.")

if __name__ == "__main__":
    main()

