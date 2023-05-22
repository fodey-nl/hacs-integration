from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
import logging
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity
)
from pyfodey.api import (
    API,
    AuthorizationFailed,
    RequestFailed
)
from .const import DOMAIN
from datetime import timedelta

from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    coordinator = FodeyCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [FodeyDeviceEntity(coordinator, device_id) for device_id in coordinator.data],
        True
    )


class FodeyCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, api: API):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Fodey",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        try:
            devices = {}
            async for device in self.api.devices():
                devices[device["id"]] = await self.api.device_details(device["id"])

            return devices
        except AuthorizationFailed as err:
            raise ConfigEntryAuthFailed from err
        except RequestFailed as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


class FodeyDeviceEntity(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator, device_id) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._name = None
        self._latitude = None
        self._longitude = None
        self._battery = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data[self._device_id]
        if not data or "device" not in data:
            return None

        device = data["device"]

        if "vehicleLicensePlate" in device:
            self._name = device["vehicleLicensePlate"]
        elif "imei" in device:
            self._name = device["imei"]

        last_position = data["last_position"]

        if "latitude" in last_position:
            self._latitude = last_position["latitude"]

        if "longitude" in last_position:
            self._longitude = last_position["longitude"]

        self.async_write_ha_state()

    @property
    def unique_id(self):
        """Return unique ID of the entity."""
        return self._device_id

    @property
    def battery_level(self):
        """Return battery value of the device."""
        return self._battery

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._latitude

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._longitude

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS
