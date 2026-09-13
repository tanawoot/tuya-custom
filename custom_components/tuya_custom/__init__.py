"""Tuya Custom Integration with Lock and ZHA Custom Quirk Support."""
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LOCK]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tuya Custom from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Point zhaquirks strictly to the 'quirks' subfolder
    quirks_dir = os.path.join(os.path.dirname(__file__), "quirks")
    if os.path.exists(quirks_dir):
        try:
            import zhaquirks

            # ใช้ async_add_executor_job เพื่อไม่ให้ Block Event Loop ของ Home Assistant
            await hass.async_add_executor_job(zhaquirks.setup, quirks_dir)
            _LOGGER.info("Successfully registered ZHA custom quirks from %s", quirks_dir)
        except Exception as err:
            _LOGGER.warning("Could not register ZHA custom quirk: %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok