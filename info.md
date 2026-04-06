# OttoWilde G32 HomeAssistant Integration

Monitor your OttoWilde G32 Connected grill directly in HomeAssistant.

## Features

✅ **8 Temperature Sensors** - 4 zones + 4 probes  
✅ **Gas Level Monitoring** - Real-time percentage  
✅ **Hood & Auto-Light Sensors** - Status monitoring  
✅ **Configuration Sensors** - View grill settings  
✅ **Native HA Entities** - No MQTT broker required  
✅ **Cloud Compatible** - Mobile app keeps working  
✅ **Real-time Updates** - ~4 second refresh rate  

## Requirements

⚠️ **UniFi Router with SSH Access Required**

This integration requires a UniFi router to configure DNS redirection. The grill must connect through your HomeAssistant instance to extract sensor data.

## Installation Steps

1. **Install via HACS** (this integration)
2. **Configure UniFi DNS redirect** (see README)
3. **Add integration** in HA Settings → Integrations
4. **Power cycle grill** to connect through proxy

Full setup instructions in [README](https://github.com/FabianLuft/OttoWildeG32).

## How It Works

```
Grill → HomeAssistant Proxy → HA Entities
                ↓
           Cloud (app still works!)
```

Uses MITM proxy to intercept and parse binary sensor data while maintaining cloud connectivity.

## Entities Created

**Sensors (10)**:
- 4x Zone Temperature Sensors (grill surface, 0-600°C)
- 4x Meat Probe Sensors (0-120°C)
- 1x Gas Level Sensor (percentage)
- 1x Light Sensitivity Sensor (read-only config)

**Binary Sensors (3)**:
- 1x Hood Status (open/closed)
- 1x Auto-Light Sensor (ambient light detection)
- 1x Warnings Enabled (read-only config)

**Total: 13 entities**

Unused probes show as "Unknown" until connected.
