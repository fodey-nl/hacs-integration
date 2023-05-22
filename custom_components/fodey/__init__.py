"""The Fodey GPS integration."""
from __future__ import annotations

import asyncio
import logging
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from pyfodey.api import API
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = API(hass.loop, session, entry.data[CONF_API_URL], entry.data[CONF_API_TOKEN])

    if not await api.login_validate():
        raise ConfigEntryAuthFailed

    hass.data[DOMAIN][entry.entry_id] = api

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "device_tracker")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
