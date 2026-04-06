# OttoWilde G32 Grill - HomeAssistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

HomeAssistant custom integration for the **OttoWilde G32 Connected** infrared grill. Monitor real-time temperatures, gas levels, hood status, and grill configuration directly in HomeAssistant.

## Features

- **8 Temperature Sensors**: 4 grill surface zones + 4 meat probes
- **8 Target Temperature Controls**: Automatic number entities for setting thresholds
- **8 Climate Dial Controls**: Full thermostat interface for visual temperature control
- **Gas Level Monitoring**: Real-time gas bottle percentage
- **Hood Status**: Binary sensor for hood open/closed
- **Auto-Light Sensor**: Detects when ambient light triggers automatic grill light
- **Configuration Monitoring**: Read-only sensors showing grill warnings and light sensitivity settings
- **Automatic Setup**: All entities created automatically - no manual YAML configuration needed!

All data is intercepted locally via MITM proxy and forwarded transparently to the cloud - your mobile app continues to work normally.

## Entities

After installation, you'll get these entities **automatically created**:

### Temperature Sensors (8)
- `sensor.ottowilde_g32_zone_1` through `zone_4` - Grill surface temperatures (0-600°C)
- `sensor.ottowilde_g32_probe_1` through `probe_4` - Meat probe temperatures (0-120°C)

### Target Temperature Controls (8)
- `number.ottowilde_g32_zone_1_target` through `zone_4_target` - Zone thresholds (0-600°C, step 10)
- `number.ottowilde_g32_probe_1_target` through `probe_4_target` - Probe targets (0-120°C, step 1)

### Climate Dial Controls (8)
- `climate.ottowilde_g32_zone_1_dial` through `zone_4_dial` - Zone thermostat interface
- `climate.ottowilde_g32_probe_1_dial` through `probe_4_dial` - Probe thermostat interface

### Other Sensors (2)
- `sensor.ottowilde_g32_gas_level` - Gas bottle percentage (0-100%)
- `sensor.ottowilde_g32_light_sensitivity` - Light sensitivity level (1-3 or "Unknown")

### Binary Sensors (3)
- `binary_sensor.ottowilde_g32_hood` - Hood open/closed
- `binary_sensor.ottowilde_g32_auto_light` - Auto-light triggered (dark environment detected)
- `binary_sensor.ottowilde_g32_warnings_enabled` - Grill warnings enabled/disabled

**Total: 10 sensors + 8 number entities + 8 climate entities + 3 binary sensors = 29 entities**

## Prerequisites

### 1. UniFi Router with DNS Control

This integration requires **DNS hijacking** to redirect grill traffic through the HomeAssistant proxy. Currently tested with:
- UniFi Dream Machine (UDM)
- UniFi Security Gateway (USG)

### 2. Network Setup

Your grill must be on the same network (or routable network) as your HomeAssistant instance.

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in HomeAssistant
2. Click the 3 dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL with category "Integration"
5. Click "Install"
6. Restart HomeAssistant

### Option 2: Manual Installation

1. Download this repository
2. Copy the `custom_components/ottowilde_g32` folder to your HomeAssistant `custom_components` directory
3. Restart HomeAssistant

## Configuration

### Step 1: Configure DNS Redirect on UniFi Router

SSH into your UniFi router and run:

```bash
# Create dnsmasq configuration to redirect grill cloud traffic
echo 'address=/socket.ottowildeapp.com/<HOMEASSISTANT_IP>' >> /etc/dnsmasq.d/ottowilde.conf

# Restart dnsmasq
killall -HUP dnsmasq
```

Replace `<HOMEASSISTANT_IP>` with your HomeAssistant server's IP address (e.g., `192.168.1.100`).

**What this does**: Redirects all grill traffic destined for the OttoWilde cloud server (`socket.ottowildeapp.com`) to your HomeAssistant instance instead.

### Step 2: Add Integration in HomeAssistant

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"OttoWilde G32"**
4. Enter your grill's IP address when prompted
5. Click **Submit**

The integration will:
- Start the MITM proxy on port 4501
- Accept connections from your grill
- Parse sensor data in real-time
- Forward all traffic to the real cloud server (3.120.177.98:4501)
- **Automatically create 29 entities** under one device (sensors, thresholds, climate controls)

**No manual YAML configuration needed!** Everything is set up automatically.

### Step 3: Power Cycle Your Grill

1. Turn off your grill completely
2. Wait 10 seconds
3. Turn it back on
4. The grill will now connect through HomeAssistant

Check HomeAssistant logs - you should see:
```
INFO: ✓ New connection from grill: <GRILL_IP>:xxxxx
INFO: ✓ Connected to cloud
INFO: 📊 Grill Data → Zone 1: 15.2°C | ... | Gas: 35.0% | Hood: closed
```

## Verifying It Works

1. **Check Entities**: All 29 entities should appear under the OttoWilde G32 device
   - 8 temperature sensors
   - 8 target number entities
   - 8 climate dial entities
   - 3 binary sensors
   - 2 other sensors
2. **Test Mobile App**: Open the OttoWilde app - it should still work normally
3. **Watch Logs**: Real-time sensor data should appear in HomeAssistant logs every ~4 seconds
4. **Change Settings**: Toggle warnings in the mobile app - the `warnings_enabled` sensor should update in HA
5. **Test Climate Dials**: Open a climate entity (e.g., `climate.ottowilde_g32_zone_1_dial`) and adjust the target temperature

## Dashboard Setup

Want a beautiful circular dial interface? See [VIZ/README_DIAL.md](../VIZ/README_DIAL.md) for instructions on setting up:
- Circular gauge rings with thick borders
- Draggable temperature controls
- +/- adjustment buttons
- Tap-to-edit direct input
- Color-coded temperature indicators
- Mushroom Cards integration

Simply paste the provided YAML into a dashboard card - all entities are already created!

## Troubleshooting

### Grill Won't Connect

**Problem**: Grill doesn't connect to HomeAssistant proxy.

**Solutions**:
1. Verify DNS redirect is active:
   ```bash
   ssh admin@<router-ip>
   cat /etc/dnsmasq.d/ottowilde.conf
   ```
2. Check HomeAssistant firewall allows port 4501
3. Verify grill and HA are on same network/VLAN
4. Check HA logs for connection attempts

### Mobile App Doesn't Work

**Problem**: Mobile app shows offline or can't connect.

**Solutions**:
1. Verify proxy is forwarding traffic (check logs for "Cloud→Grill" messages)
2. Restart the integration
3. Power cycle the grill

### Sensors Show "Unknown" or "Unavailable"

**Problem**: Entities exist but show no data.

**Solutions**:
1. Check logs for "📊 Grill Data" entries
2. Verify grill is powered on and connected
3. Wait ~10 seconds for first sensor packet
4. Restart integration if needed

### Temperature Readings Wrong

**Problem**: Temperatures don't match mobile app.

**Current Formula** (verified correct):
- Zones (grill surface): raw ÷ 20 = °C
- Probes (meat): raw ÷ 10 = °C

If readings are still wrong, please open an issue with:
- Mobile app reading
- HomeAssistant sensor reading
- Raw packet hex (from logs)

### Configuration Sensors Not Updating

**Problem**: `warnings_enabled` or `light_sensitivity` show "Unknown".

**Explanation**: These sensors update only when the mobile app sends configuration changes to the grill. They're **read-only** and display the last-known state.

**To update**:
1. Open mobile app
2. Change a setting (toggle warnings or adjust light sensitivity)
3. Configuration sensors should update in HA within seconds

## Advanced: Protocol Documentation

Want to understand how this works? See [PROTOCOL.md](PROTOCOL.md) for complete reverse-engineered protocol documentation including:
- 50-byte sensor packet structure
- 9-byte configuration handshake format
- Temperature encoding rationale
- Gas level calculation
- All byte-by-byte breakdowns

## Limitations

- **Read-only configuration**: You cannot change grill settings from HomeAssistant (warnings, light sensitivity, etc.). Use the mobile app for configuration.
- **Requires DNS redirect**: Cannot work without redirecting grill traffic through HA
- **UniFi routers only**: Currently only tested with UniFi routers that support dnsmasq
- **Single grill**: Integration assumes one grill per HA instance

## Safety & Privacy

- All traffic is forwarded transparently to the cloud - no data is modified
- Your mobile app continues to work normally
- No credentials or cloud API keys needed
- Proxy only reads sensor data, does not control grill operation
- Protocol is unencrypted TCP (no HTTPS/TLS observed)

## Contributing

Found a bug or want to contribute? Please open an issue or pull request!

### Protocol Research

If you discover new protocol features, please share:
1. Raw packet hex (from logs with `_LOGGER.debug` enabled)
2. What the mobile app was showing at that time
3. Any settings changed in the app

## Support

- **Issues**: [GitHub Issues](https://github.com/FabianLuft/OttoWildeG32/issues)
- **Documentation**: [PROTOCOL.md](PROTOCOL.md)
- **Community**: HomeAssistant forums

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, endorsed by, or supported by OttoWilde. Use at your own risk. The integration intercepts network traffic and may violate warranty terms.

---

**Enjoy grilling with HomeAssistant! 🔥**
