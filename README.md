# Rideau Canal Sensor Simulation

## Overview

This Python application simulates IoT sensors at three locations along the Rideau Canal Skateway: Dow's Lake, Fifth Avenue, and NAC (National Arts Centre). The simulator sends realistic sensor data to Azure IoT Hub every 10 seconds, including ice thickness, surface temperature, snow accumulation, and external temperature measurements.

## Technologies Used

- **Python 3.8+** - Programming language
- **Azure IoT Device SDK** - Communication with Azure IoT Hub
- **python-dotenv** - Environment variable management
- **json** - Data serialization
- **datetime** - Timestamp generation

## Prerequisites

- Python 3.8 or higher installed
- Azure account with IoT Hub created
- Three devices registered in Azure IoT Hub
- Device connection strings for each location

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/rideau-canal-sensor-simulation.git
   cd rideau-canal-sensor-simulation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your device connection strings:
   ```
   DOWS_LAKE_CONNECTION_STRING=HostName=...;DeviceId=dows-lake;SharedAccessKey=...
   FIFTH_AVENUE_CONNECTION_STRING=HostName=...;DeviceId=fifth-avenue;SharedAccessKey=...
   NAC_CONNECTION_STRING=HostName=...;DeviceId=nac;SharedAccessKey=...
   ```

## Configuration

### Environment Variables

The application requires connection strings for three devices:

- `DOWS_LAKE_CONNECTION_STRING` - Connection string for Dow's Lake sensor
- `FIFTH_AVENUE_CONNECTION_STRING` - Connection string for Fifth Avenue sensor
- `NAC_CONNECTION_STRING` - Connection string for NAC sensor

### Sensor Configuration (Optional)

You can customize sensor behavior by editing `config/sensor_config.json`:

```json
{
  "locations": {
    "dows-lake": {
      "iceThickness": {"min": 20, "max": 40, "variation": 2},
      "surfaceTemperature": {"min": -10, "max": 0, "variation": 1},
      "snowAccumulation": {"min": 0, "max": 15, "variation": 1},
      "externalTemperature": {"min": -15, "max": 5, "variation": 2}
    }
  },
  "sendInterval": 10
}
```

## Usage

### Basic Usage

Run the simulator:
```bash
python sensor_simulator.py
```

The simulator will start sending data from all three locations every 10 seconds.

### Running Individual Sensors

To run only one sensor:
```bash
python sensor_simulator.py --location dows-lake
python sensor_simulator.py --location fifth-avenue
python sensor_simulator.py --location nac
```

### Verbose Mode

Enable detailed logging:
```bash
python sensor_simulator.py --verbose
```

## Code Structure

### Main Components

#### `sensor_simulator.py`
Main entry point that:
- Initializes IoT Hub clients for each location
- Generates realistic sensor data
- Sends messages every 10 seconds
- Handles errors and reconnection

#### Key Functions

- `generate_sensor_data(location)` - Generates realistic sensor readings based on location
- `send_telemetry(client, location, data)` - Sends data to IoT Hub
- `create_client(connection_string)` - Creates and connects IoT Hub client

### Sensor Data Generation

The simulator generates realistic data with:
- **Ice Thickness:** 20-40 cm with gradual changes
- **Surface Temperature:** -10°C to 0°C (winter conditions)
- **Snow Accumulation:** 0-15 cm with occasional increases
- **External Temperature:** -15°C to 5°C (ambient conditions)

Data includes realistic variations and gradual changes over time to simulate real-world conditions.

## Sensor Data Format

### JSON Schema

Each message sent to IoT Hub follows this structure:

```json
{
  "deviceId": "dows-lake",
  "location": "Dow's Lake",
  "timestamp": "2025-01-15T14:30:00Z",
  "iceThickness": 32.5,
  "surfaceTemperature": -3.2,
  "snowAccumulation": 5.1,
  "externalTemperature": -8.5
}
```

### Field Descriptions

- `deviceId` - Unique device identifier (dows-lake, fifth-avenue, nac)
- `location` - Human-readable location name
- `timestamp` - ISO 8601 formatted UTC timestamp
- `iceThickness` - Ice thickness in centimeters (float)
- `surfaceTemperature` - Surface temperature in Celsius (float)
- `snowAccumulation` - Snow depth in centimeters (float)
- `externalTemperature` - Ambient air temperature in Celsius (float)

### Example Output

```json
{
  "deviceId": "fifth-avenue",
  "location": "Fifth Avenue",
  "timestamp": "2025-01-15T14:30:10Z",
  "iceThickness": 28.3,
  "surfaceTemperature": -1.8,
  "snowAccumulation": 3.2,
  "externalTemperature": -6.1
}
```

## Troubleshooting

### Common Issues

#### 1. Connection Failed Error

**Problem:** `Connection failed: [error message]`

**Solutions:**
- Verify connection strings in `.env` file
- Check device registration in Azure IoT Hub
- Ensure IoT Hub is running and accessible
- Verify network connectivity

#### 2. Module Not Found Error

**Problem:** `ModuleNotFoundError: No module named 'azure.iot.device'`

**Solution:**
```bash
pip install -r requirements.txt
```

#### 3. Invalid Connection String

**Problem:** `Invalid connection string format`

**Solution:**
- Ensure connection string includes: `HostName`, `DeviceId`, and `SharedAccessKey`
- Check for typos or missing semicolons
- Verify connection string from Azure Portal

#### 4. Data Not Appearing in IoT Hub

**Problem:** Messages sent but not visible in IoT Hub

**Solutions:**
- Check IoT Hub metrics in Azure Portal
- Verify message routing is configured
- Check device permissions
- Review IoT Hub logs

#### 5. High CPU Usage

**Problem:** Simulator using too much CPU

**Solution:**
- Reduce send frequency (modify `SEND_INTERVAL` in code)
- Check for infinite loops in error handling
- Ensure proper sleep intervals between sends

### Debug Mode

Enable debug logging:
```bash
python sensor_simulator.py --debug
```

This will print detailed information about:
- Connection attempts
- Message payloads
- Error details
- Retry attempts

## Testing

### Manual Testing

1. Start the simulator
2. Monitor Azure IoT Hub metrics
3. Verify messages are received
4. Check message content in IoT Hub message explorer

### Automated Testing

Run unit tests (if available):
```bash
python -m pytest tests/
```

## Performance

- **Message Frequency:** 1 message per sensor every 10 seconds
- **Total Throughput:** 18 messages per minute (3 sensors)
- **Message Size:** ~200 bytes per message
- **Network Usage:** ~3.6 KB per minute

## Security Notes

- **Never commit `.env` file** - Contains sensitive connection strings
- **Use device-specific keys** - Each sensor has its own connection string
- **Rotate keys regularly** - For production deployments
- **Monitor access logs** - Check for unauthorized access

## License

This project is created for educational purposes as part of CST8916 course requirements.

