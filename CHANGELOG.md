# Changelog

## [1.1.0] - 2026-04-06

### Added
- **Automatic entity creation** - no manual YAML configuration required!
- **Number entities** (8 total):
  - Zone target temperatures: `number.ottowilde_g32_zone_1_target` through `zone_4_target`
    - Range: 0-600°C, step 10°C, default 300°C
  - Probe target temperatures: `number.ottowilde_g32_probe_1_target` through `probe_4_target`
    - Range: 0-120°C, step 1°C, default 60°C
- **Climate entities** (8 total):
  - Zone dial controls: `climate.ottowilde_g32_zone_1_dial` through `zone_4_dial`
  - Probe dial controls: `climate.ottowilde_g32_probe_1_dial` through `probe_4_dial`
  - Full thermostat interface with draggable controls
  - Works seamlessly with mushroom-thermostat-card
- New platforms: `number.py` and `climate.py`

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
- `number.ottowilde_g32_zone_1_target`
- `climate.ottowilde_g32_zone_1_dial`

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
