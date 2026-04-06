# OttoWilde G32 Protocol Documentation

## Overview

The OttoWilde G32 Connected grill uses a bidirectional TCP protocol over port 4501 to communicate with the cloud server at `3.120.177.98:4501`. The protocol consists of two distinct message types:

1. **50-byte Sensor Packets** (Grill → Cloud) - Real-time sensor data
2. **9-byte Configuration Handshakes** (Cloud → Grill) - Configuration settings from mobile app

## Data Flow Architecture

```
┌─────────────────┐
│  Mobile App     │
│  (iOS/Android)  │
└────────┬────────┘
         │ HTTPS/WebSocket
         ▼
┌─────────────────┐
│  Cloud Server   │
│ 3.120.177.98    │
│   Port 4501     │
└────────┬────────┘
         │ TCP Binary Protocol
         ▼
┌─────────────────┐
│ HomeAssistant   │
│  MITM Proxy     │ ◄── Intercepts & Parses
└────────┬────────┘
         │ TCP Forwarding
         ▼
┌─────────────────┐
│  OttoWilde G32  │
│     Grill       │
│  (WiFi Module)  │
└─────────────────┘
```

### Traffic Patterns

**Upstream (Grill → Cloud → App)**:
- Grill sends 50-byte sensor packets every ~4 seconds
- Contains: temperatures, gas level, hood status, light sensor state
- Forwarded to cloud, which relays to mobile app

**Downstream (App → Cloud → Grill)**:
- Mobile app sends configuration changes via cloud
- Cloud forwards as 9-byte handshake messages
- Contains: warnings enabled, light sensitivity settings
- Grill receives and applies configuration

---

## 50-Byte Sensor Packet Structure

### Packet Format

| Byte(s) | Field | Type | Description | Formula |
|---------|-------|------|-------------|---------|
| 0-1 | Header | Fixed | Always `0xa3 0x3a` | - |
| 2-5 | Serial | 4 bytes | Grill serial number | Hex string |
| 6-7 | Zone 1 | uint16 BE | Grill surface zone 1 temp | raw ÷ 20 = °C |
| 8-9 | Zone 2 | uint16 BE | Grill surface zone 2 temp | raw ÷ 20 = °C |
| 10-11 | Zone 3 | uint16 BE | Grill surface zone 3 temp | raw ÷ 20 = °C |
| 12-13 | Zone 4 | uint16 BE | Grill surface zone 4 temp | raw ÷ 20 = °C |
| 14-15 | Probe 1 | uint16 BE | Meat probe 1 temp | raw ÷ 10 = °C |
| 16-17 | Probe 2 | uint16 BE | Meat probe 2 temp | raw ÷ 10 = °C |
| 18-19 | Probe 3 | uint16 BE | Meat probe 3 temp | raw ÷ 10 = °C |
| 20-21 | Probe 4 | uint16 BE | Meat probe 4 temp | raw ÷ 10 = °C |
| 22-23 | Gas Level | uint16 BE | Gas bottle percentage | raw ÷ 112 = % |
| 24 | Hood Status | uint8 | Hood open/closed | 0=closed, 1=open |
| 25 | Auto-Light | uint8 | Light sensor activation | 0=inactive, 1=active |
| 26-48 | Unknown | 23 bytes | Additional data (undocumented) | - |
| 49 | End Marker | Fixed | Always `0xc3` | - |

### Temperature Encoding Rationale

The protocol uses **different divisors** for zones vs probes based on their operating ranges:

- **Zones (÷20)**: Grill surface temperatures range 0-600°C for infrared grilling
  - 16-bit max: 65535 ÷ 20 = 3276°C (sufficient headroom)
  - Precision: 0.05°C steps
  
- **Probes (÷10)**: Meat temperatures range 0-120°C
  - 16-bit max: 65535 ÷ 10 = 6553°C (more than needed)
  - Precision: 0.1°C steps (better resolution for food temps)

This encoding optimizes data size (2 bytes per sensor) while maintaining appropriate precision for each sensor type.

### Unused Sensor Marker

- Raw value `0x9600` (38400 decimal) indicates sensor is not connected/active
- Skip parsing when this value is detected

### Example Packet

**Hex**: `a33aAABBCCDD01280128011e011e005a0050005a005a0f4f00000d010405c423012c01000331d0de67000000002af80001c3`

**Parsed Data**:
- Serial: `AABBCCDD`
- Zone 1: `0x0128` (296) → 296÷20 = **14.8°C**
- Zone 2: `0x0128` (296) → 296÷20 = **14.8°C**
- Zone 3: `0x011e` (286) → 286÷20 = **14.3°C**
- Zone 4: `0x011e` (286) → 286÷20 = **14.3°C**
- Probe 1: `0x005a` (90) → 90÷10 = **9.0°C**
- Probe 2: `0x0050` (80) → 80÷10 = **8.0°C**
- Probe 3: `0x005a` (90) → 90÷10 = **9.0°C**
- Probe 4: `0x005a` (90) → 90÷10 = **9.0°C**
- Gas: `0x0f4f` (3919) → 3919÷112 = **35.0%**
- Hood: `0x00` → **Closed**
- Auto-Light: `0x00` → **Inactive**

---

## 9-Byte Configuration Handshake Structure

### Packet Format

| Byte | Field | Description | Values |
|------|-------|-------------|--------|
| 0 | Header | Always `0x3c` | Fixed |
| 1-4 | Serial | Grill serial number (4 bytes) | Matches sensor packet |
| 5 | Config Flags | Configuration bitfield | See below |
| 6 | Config Extended | Extended config (usually `0x00`) | Reserved |
| 7 | Settings Value | Light sensitivity / other settings | See below |
| 8 | End Marker | Always `0xc3` | Fixed |

### Byte 5: Configuration Flags

| Bit | Setting | Description |
|-----|---------|-------------|
| 0 | Warnings | 1 = Grill warnings enabled, 0 = disabled |
| 1-7 | Unknown | Reserved/undocumented |

**Examples**:
- `0x0b` (binary: `00001011`) = Warnings **enabled**
- `0x0c` (binary: `00001100`) = Warnings **disabled**

### Byte 7: Settings Value

| Value (Hex) | Value (Dec) | Setting | Description |
|-------------|-------------|---------|-------------|
| `0x00` | 0 | Default | Warnings disabled state |
| `0x01` | 1 | Special | Live activities disabled |
| `0x14` | 20 | Default | Standard value when warnings enabled |
| `0x24` | 36 | Light Level 1 | Lowest light sensitivity |
| `0x28` | 40 | Light Level 2 | Medium light sensitivity (+4) |
| `0x2c` | 44 | Light Level 3 | Highest light sensitivity (+8) |

**Pattern**: Light sensitivity values increment by **4** (36 → 40 → 44)

### Example Handshakes

| Hex Packet | Serial | Config Flags | Settings | Decoded Meaning |
|------------|--------|--------------|----------|-----------------|
| `3cAABBCCDD0b0014c3` | AABBCCDD | `0x0b` | `0x14` (20) | Warnings **ON**, default settings |
| `3cAABBCCDD0c0000c3` | AABBCCDD | `0x0c` | `0x00` (0) | Warnings **OFF** |
| `3cAABBCCDD0c0001c3` | AABBCCDD | `0x0c` | `0x01` (1) | Live activities disabled |
| `3cAABBCCDD0b0024c3` | AABBCCDD | `0x0b` | `0x24` (36) | Light sensitivity = **1** (low) |
| `3cAABBCCDD0b0028c3` | AABBCCDD | `0x0b` | `0x28` (40) | Light sensitivity = **2** (medium) |
| `3cAABBCCDD0b002cc3` | AABBCCDD | `0x0b` | `0x2c` (44) | Light sensitivity = **3** (high) |

---

## Implementation Notes

### Parsing Code (Python)

```python
import struct

def parse_sensor_packet(data: bytes) -> dict:
    """Parse 50-byte sensor packet."""
    if len(data) != 50 or data[0:2] != b'\xa3\x3a' or data[49] != 0xc3:
        return None
    
    result = {'serial': data[2:6].hex(), 'zones': {}, 'probes': {}}
    
    # Parse temperatures (8 sensors)
    for i in range(8):
        offset = 6 + (i * 2)
        raw = struct.unpack('>H', data[offset:offset+2])[0]
        
        if raw == 0x9600:  # Unused sensor
            continue
        
        if i < 4:  # Zones (grill surface)
            temp_c = raw / 20.0
            result['zones'][f'zone_{i+1}'] = round(temp_c, 1)
        else:  # Probes (meat)
            temp_c = raw / 10.0
            result['probes'][f'probe_{i-3}'] = round(temp_c, 1)
    
    # Gas level
    gas_raw = struct.unpack('>H', data[22:24])[0]
    result['gas_level'] = round(gas_raw / 112.0, 1)
    
    # Status
    result['hood_open'] = bool(data[24])
    result['auto_light_triggered'] = bool(data[25])
    
    return result

def parse_handshake(data: bytes) -> dict:
    """Parse 9-byte configuration handshake."""
    if len(data) != 9 or data[0] != 0x3c or data[8] != 0xc3:
        return None
    
    result = {
        'serial': data[1:5].hex(),
        'warnings_enabled': bool(data[5] & 0x01),
        'settings_value': data[7]
    }
    
    # Decode light sensitivity (36, 40, 44 = levels 1, 2, 3)
    settings_val = data[7]
    if 0x24 <= settings_val <= 0x2c and (settings_val - 0x24) % 4 == 0:
        result['light_sensitivity'] = ((settings_val - 0x24) // 4) + 1
    
    return result
```

### MITM Proxy Requirements

1. **DNS Hijacking**: Redirect `socket.ottowildeapp.com` to proxy IP
2. **Transparent Forwarding**: All packets must be forwarded unchanged
3. **Bidirectional**: Handle both upstream (sensor) and downstream (config) traffic
4. **Keep-Alive**: Maintain persistent TCP connections
5. **Error Handling**: Reconnect on connection loss

### Security Considerations

- No encryption observed in protocol (plain TCP)
- Serial number transmitted in cleartext
- No authentication between grill and cloud
- MITM proxy can read all sensor data and configuration

---

## Reverse Engineering Methodology

This protocol was decoded through:
1. **Packet capture** (tcpdump/Wireshark) of grill ↔ cloud traffic
2. **Binary analysis** of fixed-length messages
3. **Empirical testing** by changing app settings and observing hex changes
4. **Formula derivation** by correlating raw values with app-displayed readings

### Key Discoveries

- **Temperature divisors**: Determined by testing with known app readings (zones ÷20, probes ÷10)
- **Gas formula**: Raw value directly encodes percentage (÷112), not weight
- **Auto-light sensor**: Byte 25 indicates light sensor activation, not physical light state
- **Handshake protocol**: Discovered by toggling app settings and capturing hex changes

---

## Future Research

### Unknown Fields (Bytes 26-48)

23 bytes of undocumented data remain in the sensor packet. Possible candidates:

- Flame sensor readings
- Internal electronics temperature
- WiFi signal strength
- Firmware version
- Error codes / diagnostics
- Timestamps
- Ignition status
- Fan speed (if applicable)

### Potential Control Commands

The protocol appears to be **read-only** from the grill's perspective (sensor reporting) with **write** capability only from cloud (configuration). Sending custom configuration handshakes from HomeAssistant is possible but **not recommended** without full protocol understanding:

- Unknown validation rules
- Safety implications of incorrect settings
- Potential conflicts with mobile app
- Risk of bricking grill firmware

**Recommendation**: Implement **read-only** sensors in HomeAssistant. Use mobile app for configuration.

---

## References

- Cloud Server: `3.120.177.98:4501`
- DNS: `socket.ottowildeapp.com` (points to cloud)
- Grill Model: OttoWilde G32 Connected
- Protocol: TCP binary (no encryption)

---

*Document Version: 2.0*  
*Last Updated: 2026-04-06*  
*Reverse Engineered by: HomeAssistant Community*
