"""
Rideau Canal Sensor Simulator
Simulates IoT sensors at three locations: Dow's Lake, Fifth Avenue, and NAC
Sends sensor data to Azure IoT Hub every 10 seconds
"""

import asyncio
import json
import os
import random
import sys
import time
import warnings
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from azure.iot.device import IoTHubDeviceClient
from dotenv import load_dotenv

# Suppress background thread warnings and reduce logging noise
logging.getLogger("azure.iot.device").setLevel(logging.ERROR)
logging.getLogger("azure.iot.device.common").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)

# Try to import IoTHubError, fallback to Exception if not available
try:
    from azure.iot.device.exceptions import IoTHubError
except ImportError:
    # For newer SDK versions, use generic Exception
    IoTHubError = Exception

# Load environment variables
load_dotenv()

# Configuration
SEND_INTERVAL = 10  # seconds
LOCATIONS = {
    "dows-lake": {
        "name": "Dow's Lake",
        "connection_string": os.getenv("DOWS_LAKE_CONNECTION_STRING"),
    },
    "fifth-avenue": {
        "name": "Fifth Avenue",
        "connection_string": os.getenv("FIFTH_AVENUE_CONNECTION_STRING"),
    },
    "nac": {
        "name": "NAC",
        "connection_string": os.getenv("NAC_CONNECTION_STRING"),
    },
}

# Sensor data ranges (realistic winter conditions)
SENSOR_RANGES = {
    "iceThickness": {"min": 20, "max": 40, "variation": 2},
    "surfaceTemperature": {"min": -10, "max": 0, "variation": 1},
    "snowAccumulation": {"min": 0, "max": 15, "variation": 1},
    "externalTemperature": {"min": -15, "max": 5, "variation": 2},
}

# Store current sensor values for gradual changes
current_values: Dict[str, Dict[str, float]] = {}


def generate_sensor_data(location: str) -> Dict:
    """
    Generate realistic sensor data for a location.
    Values change gradually to simulate real-world conditions.
    
    Args:
        location: Location identifier (dows-lake, fifth-avenue, nac)
    
    Returns:
        Dictionary containing sensor readings
    """
    # Initialize current values if not exists
    if location not in current_values:
        current_values[location] = {
            "iceThickness": random.uniform(25, 35),
            "surfaceTemperature": random.uniform(-5, -2),
            "snowAccumulation": random.uniform(0, 10),
            "externalTemperature": random.uniform(-10, -2),
        }
    
    # Get current values
    values = current_values[location]
    
    # Generate new values with gradual changes
    for sensor, range_config in SENSOR_RANGES.items():
        current = values[sensor]
        min_val = range_config["min"]
        max_val = range_config["max"]
        variation = range_config["variation"]
        
        # Add random variation within allowed range
        change = random.uniform(-variation, variation)
        new_value = current + change
        
        # Clamp to valid range
        new_value = max(min_val, min(max_val, new_value))
        
        # Special handling for snow accumulation (can only increase or decrease slightly)
        if sensor == "snowAccumulation":
            # Snow can increase more than decrease
            if change > 0:
                new_value = min(max_val, current + random.uniform(0, variation * 1.5))
            else:
                new_value = max(min_val, current - random.uniform(0, variation * 0.5))
        
        values[sensor] = round(new_value, 1)
    
    # Create message payload
    message = {
        "deviceId": location,
        "location": LOCATIONS[location]["name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "iceThickness": values["iceThickness"],
        "surfaceTemperature": values["surfaceTemperature"],
        "snowAccumulation": values["snowAccumulation"],
        "externalTemperature": values["externalTemperature"],
    }
    
    return message


def create_client(connection_string: str) -> Optional[IoTHubDeviceClient]:
    """
    Create and connect an IoT Hub device client.
    
    Args:
        connection_string: Device connection string from Azure IoT Hub
    
    Returns:
        Connected IoTHubDeviceClient or None if connection fails
    """
    if not connection_string:
        print(f"Error: Connection string not found in environment variables")
        return None
    
    try:
        client = IoTHubDeviceClient.create_from_connection_string(connection_string)
        client.connect()
        return client
    except Exception as e:
        print(f"Error creating client: {str(e)}")
        return None


async def send_telemetry(client: IoTHubDeviceClient, location: str, data: Dict, connection_string: str):
    """
    Send telemetry data to IoT Hub with reconnection logic.
    
    Args:
        client: IoT Hub device client
        location: Location identifier
        data: Sensor data dictionary
        connection_string: Connection string for reconnection if needed
    """
    try:
        # Check if client is connected, reconnect if not
        try:
            if not client.connected:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Reconnecting {LOCATIONS[location]['name']}...")
                client.connect()
        except:
            # If connection check fails, try to reconnect
            try:
                client.disconnect()
            except:
                pass
            try:
                client.connect()
            except Exception as e:
                print(f"Warning: Could not reconnect {location}: {str(e)}")
                return
        
        # Send the message
        message_json = json.dumps(data)
        client.send_message(message_json)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {LOCATIONS[location]['name']}: "
              f"Ice={data['iceThickness']}cm, "
              f"Surface={data['surfaceTemperature']}°C, "
              f"Snow={data['snowAccumulation']}cm, "
              f"External={data['externalTemperature']}°C")
    except IoTHubError as e:
        # Try to reconnect and send again
        try:
            if "not connected" in str(e).lower():
                client.connect()
                message_json = json.dumps(data)
                client.send_message(message_json)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {LOCATIONS[location]['name']}: "
                      f"Ice={data['iceThickness']}cm, "
                      f"Surface={data['surfaceTemperature']}°C, "
                      f"Snow={data['snowAccumulation']}cm, "
                      f"External={data['externalTemperature']}°C")
            else:
                print(f"Error sending message from {location}: {str(e)}")
        except:
            print(f"Error sending message from {location}: {str(e)}")
    except Exception as e:
        # Suppress connection drop errors from background threads
        if "ConnectionDroppedError" not in str(type(e).__name__):
            print(f"Unexpected error sending message from {location}: {str(e)}")


async def run_sensor(location: str, client: IoTHubDeviceClient):
    """
    Run sensor simulation loop for a location.
    
    Args:
        location: Location identifier
        client: IoT Hub device client
    """
    print(f"Starting sensor simulation for {LOCATIONS[location]['name']}...")
    connection_string = LOCATIONS[location]["connection_string"]
    
    while True:
        try:
            # Generate sensor data
            data = generate_sensor_data(location)
            
            # Send to IoT Hub (with reconnection logic)
            await send_telemetry(client, location, data, connection_string)
            
            # Wait for next interval
            await asyncio.sleep(SEND_INTERVAL)
            
        except KeyboardInterrupt:
            print(f"\nStopping sensor for {LOCATIONS[location]['name']}...")
            break
        except Exception as e:
            # Suppress background thread connection drop errors
            if "ConnectionDroppedError" not in str(type(e).__name__):
                print(f"Error in sensor loop for {location}: {str(e)}")
            await asyncio.sleep(SEND_INTERVAL)


async def main():
    """Main function to run sensor simulations."""
    print("=" * 60)
    print("Rideau Canal Sensor Simulator")
    print("=" * 60)
    print()
    
    # Parse command line arguments
    selected_locations = []
    if len(sys.argv) > 1:
        location_arg = sys.argv[1]
        if location_arg.startswith("--location="):
            location_arg = location_arg.split("=")[1]
        elif location_arg == "--location" and len(sys.argv) > 2:
            location_arg = sys.argv[2]
        else:
            location_arg = location_arg.replace("--", "")
        
        if location_arg in LOCATIONS:
            selected_locations = [location_arg]
        else:
            print(f"Error: Unknown location '{location_arg}'")
            print(f"Available locations: {', '.join(LOCATIONS.keys())}")
            sys.exit(1)
    else:
        selected_locations = list(LOCATIONS.keys())
    
    # Create clients for selected locations
    clients = {}
    for location in selected_locations:
        connection_string = LOCATIONS[location]["connection_string"]
        client = create_client(connection_string)
        if client:
            clients[location] = client
        else:
            print(f"Warning: Failed to create client for {location}")
    
    if not clients:
        print("Error: No clients created. Check your connection strings.")
        sys.exit(1)
    
    print(f"\nRunning {len(clients)} sensor(s)...")
    print(f"Send interval: {SEND_INTERVAL} seconds")
    print("Press Ctrl+C to stop\n")
    
    # Run all sensors concurrently
    try:
        tasks = [
            run_sensor(location, client)
            for location, client in clients.items()
        ]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n\nStopping all sensors...")
    finally:
        # Disconnect all clients
        for location, client in clients.items():
            try:
                client.disconnect()
                print(f"Disconnected {LOCATIONS[location]['name']}")
            except:
                pass
        print("Simulator stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")

