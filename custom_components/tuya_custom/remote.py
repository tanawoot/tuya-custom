"""Support for Tuya WiFi Universal IR Remote via tuya_custom integration."""
from __future__ import annotations

import logging
from typing import Any

from tuya_iot import TuyaDevice, TuyaDeviceManager

from homeassistant.components.remote import (
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# นำเข้าคลาสหลักและ CONST จาก integration ของพี่
from .base import TuyaEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Data Points มาตรฐานสำหรับ Tuya IR Remote (WiFi)
DP_SEND_IR = "1"
DP_LEARN_IR = "2"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tuya IR Remote device from a config entry."""
    tuya_data = hass.data[DOMAIN][entry.entry_id]
    device_manager: TuyaDeviceManager = tuya_data["device_manager"]
    
    entities: list[TuyaIrRemoteEntity] = []
    
    for device in tuya_data["devices"]:
        # ตรวจสอบ category หรือ DP ที่ตรงกับ IR Remote (เช่น wsn, yzk หรือ pwla5warkrwbza0m)
        if device.category in ["wsn", "yzk"] or DP_SEND_IR in device.status:
            entities.append(TuyaIrRemoteEntity(device, device_manager))

    async_add_entities(entities)


class TuyaIrRemoteEntity(TuyaEntity, RemoteEntity):
    """Tuya WiFi Universal IR Remote Entity."""

    _attr_supported_features = RemoteEntityFeature.LEARN_COMMAND

    def __init__(
        self,
        device: TuyaDevice,
        device_manager: TuyaDeviceManager,
    ) -> None:
        """Initialize the Tuya IR Remote entity."""
        super().__init__(device, device_manager)
        self._attr_unique_id = f"tuya_ir_{device.id}"
        self._attr_name = device.name

    @property
    def is_on(self) -> bool:
        """Return True if remote is online and ready."""
        return self.device.online

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on remote service (if applicable)."""
        _LOGGER.debug("Tuya IR Remote %s turned on", self.name)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off remote service."""
        _LOGGER.debug("Tuya IR Remote %s turned off", self.name)
        self.async_write_ha_state()

    async def async_send_command(
        self,
        command: iterable[str],
        **kwargs: Any,
    ) -> None:
        """Send IR Base64 codes to Tuya Device."""
        for code in command:
            _LOGGER.debug("Sending IR Code via Tuya IR Remote: %s", code)
            # ส่ง payload สั่งยิงคำสั่ง IR ผ่าน Tuya Device Manager
            await self.hass.async_add_executor_job(
                self._device_manager.send_commands,
                self.device.id,
                [{"code": "ir_code", "value": code}],
            )

    async def async_learn_command(
        self,
        **kwargs: Any,
    ) -> None:
        """Trigger IR Learning mode on Tuya Device."""
        _LOGGER.info("Triggering IR Learn mode for %s", self.name)
        # ส่ง DP เพื่อเข้าสู่โหมดเรียนรู้ปุ่มรีโมท (Study/Learn Mode)
        await self.hass.async_add_executor_job(
            self._device_manager.send_commands,
            self.device.id,
            [{"code": "ir_study", "value": True}],
        )