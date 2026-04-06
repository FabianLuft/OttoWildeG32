"""OttoWilde G32 MITM Proxy for HomeAssistant Integration."""
import asyncio
import logging
import struct
import time

from homeassistant.core import HomeAssistant

from .const import CLOUD_HOST, CLOUD_PORT, DOMAIN, LOCAL_PORT

_LOGGER = logging.getLogger(__name__)


class OttoWildeProxy:
    """MITM Proxy for OttoWilde G32 - Integrated with HomeAssistant."""

    def __init__(self, hass: HomeAssistant, grill_ip: str):
        """Initialize the proxy."""
        self.hass = hass
        self.grill_ip = grill_ip
        self.server = None
        self.running = False

        # Track status changes for prominent logging
        self._last_hood_status = None

    async def start(self):
        """Start the MITM proxy server."""
        _LOGGER.info("=" * 70)
        _LOGGER.info("OttoWilde G32 MITM Proxy Starting")
        _LOGGER.info("=" * 70)
        _LOGGER.info(f"Local Port: {LOCAL_PORT}")
        _LOGGER.info(f"Cloud Server: {CLOUD_HOST}:{CLOUD_PORT}")
        _LOGGER.info(f"Expected Grill IP: {self.grill_ip}")
        _LOGGER.info("=" * 70)

        # Start TCP server
        self.server = await asyncio.start_server(
            self.handle_grill_connection,
            '0.0.0.0',
            LOCAL_PORT
        )

        addr = self.server.sockets[0].getsockname()
        _LOGGER.info(f"✓ Proxy server listening on {addr[0]}:{addr[1]}")
        _LOGGER.info("Waiting for grill to connect...")
        _LOGGER.info("(Make sure DNS redirect is configured in UniFi)")

        self.running = True

    async def stop(self):
        """Stop the proxy server."""
        _LOGGER.info("Stopping OttoWilde G32 proxy...")
        self.running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        _LOGGER.info("Proxy stopped")

    def parse_packet(self, data: bytes) -> dict | None:
        """Parse 50-byte OttoWilde sensor packet."""
        if len(data) < 50:
            return None

        # Verify header and end marker
        if data[0:2] != bytes([0xa3, 0x3a]) or data[49] != 0xc3:
            return None

        result = {
            'serial': data[2:6].hex(),
            'zones': {},
            'probes': {},
            'gas_level': None,
            'hood_open': False,
            'auto_light_triggered': False,
            'timestamp': time.time()
        }

        # Parse 8 temperature sensors (bytes 6-21)
        for i in range(8):
            offset = 6 + (i * 2)
            temp_raw = struct.unpack('>H', data[offset:offset+2])[0]

            # Skip unused sensors (0x9600 = 38400)
            if temp_raw == 0x9600:
                continue

            # Temperature calculation: zones use ÷20, probes use ÷10
            if i < 4:
                # Zones (grill surface temperatures)
                temp_c = temp_raw / 20.0
                result['zones'][f'zone_{i+1}'] = round(temp_c, 1)
            else:
                # Probes (meat/food temperatures)
                temp_c = temp_raw / 10.0
                result['probes'][f'probe_{i-3}'] = round(temp_c, 1)

            # DEBUG: Log raw hex values for temperature analysis
            sensor_type = "zone" if i < 4 else "probe"
            sensor_num = (i + 1) if i < 4 else (i - 3)
            hex_bytes = data[offset:offset+2].hex()
            _LOGGER.info(f"🔍 DEBUG: {sensor_type}_{sensor_num} | Raw hex: {hex_bytes} | Raw decimal: {temp_raw} | Calculated: {temp_c}°C")

        # Gas level (bytes 22-23) - already in percentage
        gas_raw = struct.unpack('>H', data[22:24])[0]
        result['gas_level'] = round(gas_raw / 112.0, 1)

        _LOGGER.debug(f"🔍 Gas DEBUG: raw={gas_raw} | percentage={result['gas_level']}%")

        # Status bits (bytes 24-25)
        result['hood_open'] = bool(data[24])
        result['auto_light_triggered'] = not bool(data[25])  # Inverted: 0=active (dark), 1=inactive (bright)

        return result

    def parse_handshake(self, data: bytes) -> dict | None:
        """Parse 9-byte configuration handshake from app/cloud."""
        if len(data) != 9:
            return None

        # Verify header and end marker
        if data[0] != 0x3c or data[8] != 0xc3:
            return None

        result = {
            'serial': data[1:5].hex(),
            'config_flags': data[5],
            'config_extended': data[6],
            'settings_value': data[7],
            'warnings_enabled': bool(data[5] & 0x01),
            'light_sensitivity': None,
            'raw': data.hex(),
            'timestamp': time.time()
        }

        # Decode light sensitivity (values: 36, 40, 44 = levels 1, 2, 3)
        settings_val = data[7]
        if settings_val >= 0x24 and settings_val <= 0x2c and (settings_val - 0x24) % 4 == 0:
            level = ((settings_val - 0x24) // 4) + 1
            result['light_sensitivity'] = level

        return result

    def _log_sensor_data(self, data: dict):
        """Log parsed sensor data in comprehensive, readable format."""
        # Build zones string
        if data['zones']:
            zones_str = " | ".join([f"{k.replace('_', ' ').title()}: {v}°C"
                                   for k, v in sorted(data['zones'].items())])
        else:
            zones_str = "No zones active"

        # Build probes string
        if data['probes']:
            probes_str = " | ".join([f"{k.replace('_', ' ').title()}: {v}°C"
                                    for k, v in sorted(data['probes'].items())])
        else:
            probes_str = "No probes connected"

        # Build status string
        hood_status = 'OPEN' if data['hood_open'] else 'closed'
        auto_light_status = 'ACTIVE' if data['auto_light_triggered'] else 'inactive'

        # Log with all details
        _LOGGER.info(
            f"📊 Grill Data → {zones_str} | {probes_str} | "
            f"Gas: {data['gas_level']}% | Hood: {hood_status} | Auto-Light: {auto_light_status}"
        )

        # Log status changes prominently
        if self._last_hood_status != data['hood_open']:
            _LOGGER.warning(f"🚪 Hood {'OPENED' if data['hood_open'] else 'CLOSED'}")
            self._last_hood_status = data['hood_open']

    def _update_entities(self, parsed_data: dict):
        """Update HomeAssistant entity states."""
        # Log the data first with all details
        self._log_sensor_data(parsed_data)

        # Fire HomeAssistant event for entity updates
        self.hass.bus.async_fire(
            f"{DOMAIN}_update",
            parsed_data
        )

    def _update_config_state(self, config_data: dict):
        """Fire HA event with configuration state update."""
        _LOGGER.warning(
            f"⚙️  Configuration Update: "
            f"Warnings={'ON' if config_data['warnings_enabled'] else 'OFF'} | "
            f"Light={config_data.get('light_sensitivity', 'N/A')} | "
            f"Raw: {config_data['raw']}"
        )

        # Fire HomeAssistant event for config sensor updates
        self.hass.bus.async_fire(
            f"{DOMAIN}_config_update",
            config_data
        )

    def parse_and_publish(self, data: bytes):
        """Parse sensor packets from data stream and update HA entities."""
        # Look for 50-byte packets starting with 0xa33a
        for i in range(len(data) - 49):
            if data[i:i+2] == bytes([0xa3, 0x3a]) and data[i+49] == 0xc3:
                packet = data[i:i+50]
                parsed = self.parse_packet(packet)
                if parsed:
                    self._update_entities(parsed)
                    return  # Only parse first packet in buffer

    async def forward_grill_to_cloud(self, grill_reader, cloud_writer, client_addr):
        """Forward data from grill to cloud, intercepting packets for parsing."""
        _LOGGER.info(f"[{client_addr}] Started grill→cloud forwarding")

        try:
            while True:
                data = await grill_reader.read(4096)
                if not data:
                    _LOGGER.info(f"[{client_addr}] Grill closed connection")
                    break

                _LOGGER.debug(f"[{client_addr}] Grill→Cloud: {len(data)} bytes")

                # Parse and update HA entities (non-blocking)
                try:
                    self.parse_and_publish(data)
                except Exception as e:
                    _LOGGER.error(f"Error parsing packet: {e}")

                # Forward to cloud (transparent)
                cloud_writer.write(data)
                await cloud_writer.drain()

        except Exception as e:
            _LOGGER.error(f"[{client_addr}] Grill→Cloud error: {e}")
        finally:
            _LOGGER.info(f"[{client_addr}] Stopped grill→cloud forwarding")

    async def forward_cloud_to_grill(self, cloud_reader, grill_writer, client_addr):
        """Forward cloud responses back to grill (including ACKs and handshake)."""
        _LOGGER.info(f"[{client_addr}] Started cloud→grill forwarding")

        try:
            while True:
                data = await cloud_reader.read(4096)
                if not data:
                    _LOGGER.info(f"[{client_addr}] Cloud closed connection")
                    break

                _LOGGER.debug(f"[{client_addr}] Cloud→Grill: {len(data)} bytes")

                # Detect and parse configuration handshake messages (9 bytes starting with 0x3c)
                if len(data) == 9 and data[0] == 0x3c and data[8] == 0xc3:
                    handshake = self.parse_handshake(data)
                    if handshake:
                        self._update_config_state(handshake)
                    else:
                        _LOGGER.info(f"[{client_addr}] ☁️  Cloud handshake/keep-alive: {data.hex()}")

                # Forward to grill (transparent)
                grill_writer.write(data)
                await grill_writer.drain()

        except Exception as e:
            _LOGGER.error(f"[{client_addr}] Cloud→Grill error: {e}")
        finally:
            _LOGGER.info(f"[{client_addr}] Stopped cloud→grill forwarding")

    async def handle_grill_connection(self, grill_reader, grill_writer):
        """Handle connection from grill - Main proxy logic."""
        client_addr = grill_writer.get_extra_info('peername')
        _LOGGER.info("=" * 70)
        _LOGGER.info(f"✓ New connection from grill: {client_addr}")
        _LOGGER.info("=" * 70)

        cloud_reader = None
        cloud_writer = None

        try:
            # 1. Connect to real cloud server
            _LOGGER.info(f"[{client_addr}] Connecting to cloud {CLOUD_HOST}:{CLOUD_PORT}")
            cloud_reader, cloud_writer = await asyncio.open_connection(
                CLOUD_HOST,
                CLOUD_PORT
            )
            _LOGGER.info(f"[{client_addr}] ✓ Connected to cloud")

            # 2. Start bidirectional forwarding tasks
            forward_to_cloud = asyncio.create_task(
                self.forward_grill_to_cloud(grill_reader, cloud_writer, client_addr)
            )
            forward_to_grill = asyncio.create_task(
                self.forward_cloud_to_grill(cloud_reader, grill_writer, client_addr)
            )

            # 3. Wait for either direction to close
            done, pending = await asyncio.wait(
                [forward_to_cloud, forward_to_grill],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining task
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            _LOGGER.error(f"[{client_addr}] Proxy error: {e}")

        finally:
            # Cleanup
            if grill_writer:
                grill_writer.close()
                await grill_writer.wait_closed()
            if cloud_writer:
                cloud_writer.close()
                await cloud_writer.wait_closed()

            _LOGGER.info(f"[{client_addr}] Connection closed")
