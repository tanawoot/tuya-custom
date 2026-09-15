"""Support for Tuya WiFi Universal IR Remote via tuya_custom integration."""
from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any

from homeassistant.components.remote import (
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import TuyaEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Tuya Data Points สำหรับ IR Remote
DP_SEND_IR = "1"
DP_LEARN_IR = "2"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tuya IR Remote device from a config entry."""
    tuya_data = hass.data[DOMAIN][entry.entry_id]
    
    # ดึง device_manager และรายการ devices จาก hass.data
    device_manager = tuya_data.get("device_manager")
    devices = tuya_data.get("devices", [])
    
    entities: list[TuyaIrRemoteEntity] = []
    
    for device in devices:
        status_dict = getattr(device, "status", {})
        category = getattr(device, "category", "")
        
        # เช็ก category ของ IR Remote (wsn, yzk) หรือเช็กจาก Data Point
        if category in ["wsn", "yzk"] or DP_SEND_IR in status_dict:
            entities.append(TuyaIrRemoteEntity(device, device_manager))

    async_add_entities(entities)


class TuyaIrRemoteEntity(TuyaEntity, RemoteEntity):
    """Tuya WiFi Universal IR Remote Entity."""

    _attr_supported_features = RemoteEntityFeature.LEARN_COMMAND

    def __init__(
        self,
        device: Any,
        device_manager: Any,
    ) -> None:
        """Initialize the Tuya IR Remote entity."""
        super().__init__(device, device_manager)
        device_id = getattr(device, "id", "unknown")
        device_name = getattr(device, "name", "Tuya IR Remote")
        
        self._attr_unique_id = f"tuya_ir_{device_id}"
        self._attr_name = device_name

    @property
    def is_on(self) -> bool:
        """Return True if remote is online and ready."""
        return bool(getattr(self.device, "online", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on remote service."""
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off remote service."""
        self.async_write_ha_state()

    async def async_send_command(
        self,
        command: Iterable[str],
        **kwargs: Any,
    ) -> None:
        """Send IR Base64 codes to Tuya Device."""
        for code in command:
            _LOGGER.debug("Sending IR Code via Tuya IR Remote (%s): %s", self.name, code)
            
            # เรียกใช้ send_commands ผ่าน executor job
            if hasattr(self, "device_manager") and self.device_manager:
                await self.hass.async_add_executor_job(
                    self.device_manager.send_commands,
                    self.device.id,
                    [{"code": "ir_code", "value": code}],
                )

    async def async_learn_command(
        self,
        **kwargs: Any,
    ) -> None:
        """Trigger IR Learning mode on Tuya Device."""
        _LOGGER.info("Triggering IR Learn mode for %s", self.name)
        
        if hasattr(self, "device_manager") and self.device_manager:
            await self.hass.async_add_executor_job(
                self.device_manager.send_commands,
                self.device.id,
                [{"code": "ir_study", "value": True}],
            )