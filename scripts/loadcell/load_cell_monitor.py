import serial
import serial.tools.list_ports
import json
import time
import csv
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Thread, Lock
import queue

# Configuration
SERIAL_PORT = 'COM8'
BAUD_RATE = 115200
MAX_DATA_POINTS = 500  # Number of points to keep in plot
CSV_FILENAME = f"loadcell_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# Data storage
data_lock = Lock()
force_data = deque(maxlen=MAX_DATA_POINTS)
pressure_data = deque(maxlen=MAX_DATA_POINTS)
time_data = deque(maxlen=MAX_DATA_POINTS)
all_data = []  # Store all data for CSV

# CSV file setup
csv_file = None
csv_writer = None

# Thread control
running = True

def init_csv():
    """Initialize CSV file for data storage"""
    global csv_file, csv_writer
    csv_file = open(CSV_FILENAME, 'w', newline='')
    fieldnames = ['timestamp', 'raw', 'weight_g', 'force_N', 'pressure_adc', 'pressure_v', 'scale', 'offset']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    print(f"Data will be saved to: {CSV_FILENAME}")

def save_to_csv(data):
    """Save data point to CSV"""
    global csv_writer
    if csv_writer:
        csv_writer.writerow(data)
        csv_file.flush()

def read_serial_data(ser, data_queue):
    """Read data from serial port in a separate thread (JSON format)"""
    global running
    buffer = ""
    start_time = time.time()
    
    while running:
        try:
            if ser.in_waiting > 0:
                # Read available data
                raw_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += raw_data
                
                # Process complete JSON lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line and line.startswith('{'):
                        try:
                            data = json.loads(line)
                            
                            # Handle event messages
                            if 'event' in data:
                                print(f"Arduino: {data.get('event', 'unknown')}")
                            # Handle measurement data
                            elif 'raw' in data:
                                # Calculate relative time
                                elapsed_time = time.time() - start_time
                                
                                # Store data point
                                data_point = {
                                    'timestamp': elapsed_time,
                                    'raw': data.get('raw', 0),
                                    'weight_g': data.get('weight_g', 0),
                                    'force_N': data.get('force_N', 0),
                                    'pressure_adc': data.get('pressure_adc', 0),
                                    'pressure_v': data.get('pressure_v', 0),
                                    'scale': data.get('scale', 761.654602),
                                    'offset': data.get('offset', 0)
                                }
                                
                                # Add timestamp for CSV
                                csv_data = data_point.copy()
                                csv_data['timestamp'] = datetime.now().isoformat()
                                
                                data_queue.put(data_point)
                                save_to_csv(csv_data)
                                
                        except json.JSONDecodeError as e:
                            pass  # Skip malformed JSON
                        except Exception as e:
                            pass  # Skip on any error
            
            time.sleep(0.01)  # Small delay to prevent CPU spinning
            
        except (serial.SerialException, OSError) as e:
            # Suppress errors when port is intentionally closed
            if running:
                error_msg = str(e)
                if "handle is invalid" not in error_msg.lower() and "clearcommerror" not in error_msg.lower():
                    print(f"Serial error: {e}")
            break
        except Exception as e:
            if running:
                print(f"Unexpected error in serial thread: {e}")
            break

def update_plot(frame, ax1, ax2, data_queue):
    """Update the plot with new data"""
    global force_data, pressure_data, time_data
    
    # Process all available data from queue
    new_points = 0
    while not data_queue.empty():
        try:
            data = data_queue.get_nowait()
            
            with data_lock:
                time_data.append(data['timestamp'])
                force_data.append(data['force_N'])
                pressure_data.append(data['pressure_v'])
                all_data.append(data)
            
            new_points += 1
        except queue.Empty:
            break
    
    # Update plots
    with data_lock:
        if len(time_data) > 0:
            times = list(time_data)
            forces = list(force_data)
            pressures = list(pressure_data)
            
            # Clear and redraw force plot
            ax1.clear()
            ax1.plot(times, forces, 'b-', linewidth=1.5, label='Force')
            ax1.set_xlabel('Time (s)')
            ax1.set_ylabel('Force (N)', color='b')
            ax1.tick_params(axis='y', labelcolor='b')
            ax1.grid(True, alpha=0.3)
            ax1.set_title('Live Force Measurement')
            ax1.legend(loc='upper left')
            
            # Clear and redraw pressure plot
            ax2.clear()
            ax2.plot(times, pressures, 'r-', linewidth=1.5, label='Air Pressure')
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Pressure (V)', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            ax2.grid(True, alpha=0.3)
            ax2.set_title('Live Air Pressure Measurement')
            ax2.legend(loc='upper left')
            
            # Auto-scale axes
            if len(times) > 1:
                ax1.set_xlim(max(0, times[-1] - 20), times[-1] + 1)  # Show last 60 seconds
                ax2.set_xlim(max(0, times[-1] - 20), times[-1] + 1)
    
    plt.tight_layout()
    return ax1, ax2

def main():
    """Main function"""
    global csv_file, running
    
    print("Load Cell Monitor")
    print("=" * 50)
    print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud...")
    
    # Initialize CSV
    init_csv()
    
    # Open serial port
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}")
        time.sleep(2)  # Wait for Arduino to initialize
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        print("\nAvailable ports:")
        for port in serial.tools.list_ports.comports():
            print(f"  - {port.device}")
        return
    
    # Create data queue for thread-safe communication
    data_queue = queue.Queue()
    
    # Start serial reading thread
    serial_thread = Thread(target=read_serial_data, args=(ser, data_queue), daemon=True)
    serial_thread.start()
    
    # Setup matplotlib figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    fig.suptitle('Load Cell Monitor - Live Data', fontsize=14, fontweight='bold')
    
    # Start animation
    ani = animation.FuncAnimation(fig, update_plot, fargs=(ax1, ax2, data_queue),
                                  interval=50, blit=False)  # Update every 50ms
    
    print("\nPlotting started. Close the plot window to stop.")
    print("Data is being saved to:", CSV_FILENAME)
    
    try:
        plt.show()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Stop the serial reading thread
        running = False
        
        # Give thread a moment to finish
        time.sleep(0.1)
        
        # Cleanup serial port
        try:
            if 'ser' in locals() and ser.is_open:
                ser.close()
        except Exception:
            pass
        
        # Ensure all data is saved
        if csv_file:
            csv_file.flush()  # Final flush
            csv_file.close()
            print(f"\n✓ Data saved to: {CSV_FILENAME}")
            print(f"✓ Total data points: {len(all_data)}")

if __name__ == "__main__":
    main()

