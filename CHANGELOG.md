# Changelog

## [1.2.5] - 2026-04-07

### Added
- **Grill off detection** - Sensors reset to N/A when grill stops sending data
  - 15-second timeout (grill sends every ~4s)
  - All zones → None (displayed as "N/A" in HA)
  - All probes → None (displayed as "-" in HA)
  - Automatic detection when grill is turned off

### Changed
- **Probe disconnect handling** - Probes now show "-" when physically disconnected
  - When 0x9600 marker detected, probe entity set to None
  - Differentiates between "grill off" and "probe unplugged"
  - Zones always show data when grill is on (never 0x9600)

**Impact:** Clean sensor states - no stale temperature values when grill is off or probes are removed.

## [1.2.4] - 2026-04-07

### Fixed
- **Low-temperature offset correction** - Non-linear encoding below 21°C now compensated
  - App showed 7°C, HACS showed 3°C → Fixed with offset correction
  - Formula: For temps < 21°C, apply `offset = (21 - temp) × 0.222`
  - Inflection point at 21°C (room temperature) where offset becomes 0
  - High temperatures (>21°C) continue to use simple ÷25 divisor
  - Based on empirical observation: deviation below 30°C, perfect alignment at 21°C and 62°C

**Impact:** All temperature ranges now match mobile app readings accurately, from ambient (0-30°C) to cooking (30-600°C).

**Testing needed:** User should verify accuracy at multiple points:
- 5-10°C: Low-temp accuracy
- 15-20°C: Transition region
- 25-30°C: Verify offset not over-applied
- 50-100°C: Confirm high-temp accuracy unchanged

**Note:** Coefficient (0.222) may need fine-tuning based on multi-point testing. Increase if still under-reading, decrease if over-reading.

## [1.2.3] - 2026-04-07

### Fixed
- **Unified temperature formula** - Both zones and probes now use ÷25
  - Probes were perfect with ÷25
  - Zones now also use ÷25 (changed from ÷23.4)
  - All 8 temperature sensors now use identical formula

**Impact:** All temperature sensors (zones and probes) now match mobile app readings exactly.

## [1.2.2] - 2026-04-07

### Fixed
- **Temperature formula correction** - Updated temperature divisors based on observed values
  - Zones: Changed from ÷20 to ÷23.4 (corrects 1.17x multiplier)
  - Probes: Changed from ÷10 to ÷25 (corrects 2.5x multiplier)
  - Formulas determined empirically by comparing HA readings to mobile app during operation

**Note:** Combined with v1.2.1 state_class fix, temperatures should now be accurate and stable.

## [1.2.1] - 2026-04-07

### Fixed
- **Temperature sensor drift** - Removed `state_class=MEASUREMENT` from temperature sensors
  - Temperatures were correct initially but would drift higher during heating
  - Probes showed ~2.5x actual temperature, zones showed ~1.17x actual
  - Root cause: `SensorStateClass.MEASUREMENT` is for energy/power sensors that need integration
  - Temperature sensors should NOT use state_class (matches HA core thermostats/weather sensors)
  - Gas sensor keeps state_class (correct usage for tracking tank level over time)

**Impact:** After updating to v1.2.1, temperature readings will stay accurate and won't drift during grill operation.

**Migration:** 
- Update integration via HACS
- Restart HomeAssistant or reload integration
- Temperature sensor entities will be recreated without state_class
- Historical statistics for temperature will be reset (this is intentional - old data was incorrect)

## [1.2.0] - 2026-04-07

### Removed
- **Climate entities** - Removed unnecessary climate platform
  - Removed `climate.ottowilde_g32_grill_zone_*_dial` entities (8 total)
  - Removed `climate.ottowilde_g32_grill_probe_*_dial` entities (8 total)
  - These were redundant - dashboards can access sensors and number entities directly

### Changed
- Total entities reduced from 29 to 21 (removed 8 climate entities)
- Simplified integration architecture - only essential entities remain
- Updated README with new entity count and dashboard recommendations

### Why This Change?
Climate entities were only useful for thermostat-style cards. Modern dashboard cards (like button-card) can read sensor values and control number entities directly, making the climate platform unnecessary overhead.

**Migration from 1.1.0:**
If you were using climate entities in dashboards:
- Replace with direct sensor/number entity references
- Use `lovelace_button_simple.yaml` from VIZ folder
- Example: Instead of `climate.ottowilde_g32_grill_zone_1_dial`, use:
  - Display: `sensor.ottowilde_g32_zone_1` (current temp)
  - Control: `number.ottowilde_g32_grill_zone_1_target` (tap to adjust)

## [1.1.0] - 2026-04-06

### Added
- **Automatic entity creation** - no manual YAML configuration required!
- **Number entities** (8 total):
  - Zone target temperatures: `number.ottowilde_g32_grill_zone_1_target` through `zone_4_target`
    - Range: 0-600°C, step 10°C, default 300°C
  - Probe target temperatures: `number.ottowilde_g32_grill_probe_1_target` through `probe_4_target`
    - Range: 0-120°C, step 1°C, default 60°C
- **Climate entities** (8 total) - DEPRECATED in v1.2.0
  - Zone dial controls: `climate.ottowilde_g32_grill_zone_1_dial` through `zone_4_dial`
  - Probe dial controls: `climate.ottowilde_g32_grill_probe_1_dial` through `probe_4_dial`
  - Full thermostat interface with draggable controls
  - Works seamlessly with mushroom-thermostat-card
- New platforms: `number.py` and `climate.py` (climate.py removed in v1.2.0)

### Changed
- Total entities increased from 13 to 29 (added 8 number + 8 climate entities)
- Integration now automatically creates threshold and dial control entities
- Updated README with new entity list and automatic setup instructions
- Updated dashboard YAML to use new entity IDs

### Benefits
- ✅ Zero manual configuration needed
- ✅ Clean uninstall removes all entities
- ✅ UI configurable thresholds
- ✅ Dashboard-ready climate controls
- ✅ Standard HomeAssistant architecture

### Migration from 1.0.0
If you were using manual `input_number` helpers and template climate entities:

**Old entities** (manual):
- `input_number.grill_zone_1_threshold`
- `climate.zone_1_dial` (template)

**New entities** (automatic):
- `number.ottowilde_g32_grill_zone_1_target`
- `climate.ottowilde_g32_grill_zone_1_dial`

**Migration steps**:
1. Update to v1.1.0
2. Remove manual configuration from `configuration.yaml`:
   - Delete `input_number` helpers for grill thresholds
   - Delete `template` climate entities
3. Restart HomeAssistant
4. Update dashboard YAML with new entity IDs (see `VIZ/lovelace_dial_style.yaml`)
5. Copy threshold values from old helpers to new number entities if needed

## [1.0.0] - 2026-04-05

### Initial Release
- MITM proxy with DNS redirect support
- 8 temperature sensors (4 zones, 4 probes)
- Gas level monitoring
- Hood and auto-light binary sensors
- Configuration monitoring (warnings, light sensitivity)
- Protocol documentation
- UniFi router DNS configuration guide
