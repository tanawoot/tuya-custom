"""Lock platform for Tuya Custom integration."""
import asyncio
import hashlib
import hmac
import json
import logging
import time

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ENDPOINT,
    CONF_DEVICE_ID,
    TUYA_ERROR_HINTS,
)

_LOGGER = logging.getLogger(__name__)


def generate_sign(client_id, client_secret, access_token, t, method, path, body=""):
    """Calculate Tuya Open API v2 signature matching script logic."""
    content_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    string_to_sign = f"{method}\n{content_sha256}\n\n{path}"
    sign_str = client_id + (access_token if access_token else "") + t + string_to_sign

    return (
        hmac.new(
            client_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        )
        .hexdigest()
        .upper()
    )


def _error_hint(res):
    """Retrieve hint message for known Tuya API error codes."""
    hint = TUYA_ERROR_HINTS.get(res.get("code"))
    return f" | Hint: {hint}" if hint else ""


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya Door Lock entity."""
    config = entry.data
    async_add_entities([TuyaCustomLockEntity(hass, entry, config)], True)


class TuyaCustomLockEntity(LockEntity):
    """Representation of Tuya Custom Lock Entity."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, config: dict):
        """Initialize the lock entity."""
        self.hass = hass
        self._entry = entry
        self._client_id = config[CONF_CLIENT_ID]
        self._client_secret = config[CONF_CLIENT_SECRET]
        self._endpoint = config[CONF_ENDPOINT].rstrip("/")
        self._device_id = config[CONF_DEVICE_ID]

        self._attr_name = f"Door Lock ({self._device_id[-4:]})"
        self._attr_unique_id = f"tuya_custom_lock_{self._device_id}"
        self._attr_is_locked = True

    async def _async_get_access_token(self, session):
        """Fetch Access Token asynchronously."""
        t = str(int(time.time() * 1000))
        path = "/v1.0/token?grant_type=1"
        sign = generate_sign(self._client_id, self._client_secret, "", t, "GET", path)

        headers = {
            "client_id": self._client_id,
            "sign": sign,
            "t": t,
            "sign_method": "HMAC-SHA256",
        }

        url = self._endpoint + path
        async with session.get(url, headers=headers) as response:
            res = await response.json()
            if res.get("success"):
                return res["result"]["access_token"]
            raise Exception(f"Failed to get token: {res}{_error_hint(res)}")

    async def _async_send_tuya_request(self, session, method, path, body_dict=None, token=None):
        """Send authenticated HTTP request matching script logic."""
        if not token:
            token = await self._async_get_access_token(session)

        t = str(int(time.time() * 1000))
        body_str = json.dumps(body_dict) if body_dict else ""

        sign = generate_sign(
            self._client_id, self._client_secret, token, t, method, path, body_str
        )

        headers = {
            "client_id": self._client_id,
            "access_token": token,
            "sign": sign,
            "t": t,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }

        url = self._endpoint + path
        if method == "POST":
            async with session.post(url, headers=headers, data=body_str) as response:
                return await response.json()
        else:
            async with session.get(url, headers=headers) as response:
                return await response.json()

    async def async_unlock(self, **kwargs) -> None:
        """Unlock the door and auto reset state back to locked."""
        _LOGGER.info("Starting Tuya unlock sequence...")
        session = async_get_clientsession(self.hass)

        try:
            token = await self._async_get_access_token(session)

            # Step A: Request password ticket ID
            ticket_path = f"/v1.0/devices/{self._device_id}/door-lock/password-ticket"
            ticket_res = await self._async_send_tuya_request(session, "POST", ticket_path, token=token)

            if not ticket_res.get("success"):
                _LOGGER.error("Failed to obtain ticket: %s%s", ticket_res, _error_hint(ticket_res))
                return

            ticket_id = ticket_res["result"]["ticket_id"]
            _LOGGER.info("Ticket ID obtained: %s", ticket_id)

            # Step B: Password-free remote unlock
            unlock_path = f"/v1.0/devices/{self._device_id}/door-lock/password-free/open-door"
            payload = {"ticket_id": ticket_id}

            unlock_res = await self._async_send_tuya_request(
                session, "POST", unlock_path, body_dict=payload, token=token
            )

            if unlock_res.get("success"):
                _LOGGER.info("ปลดล็อกประตูเรียบร้อยแล้วค่ะพี่!")
                
                # 1. เปลี่ยนสถานะเป็น Unlocked บน UI ให้รู้ว่าปลดล็อกสำเร็จแล้ว
                self._attr_is_locked = False
                self.async_write_ha_state()

                # 2. รอ 5 วินาที แล้วรีเซ็ตสถานะกลับมาเป็น Locked (ปุ่มล็อก) เหมือนเดิม
                await asyncio.sleep(5)
                self._attr_is_locked = True
                self.async_write_ha_state()
            else:
                _LOGGER.error("ปลดล็อกไม่สำเร็จ: %s%s", unlock_res, _error_hint(unlock_res))

        except Exception as err:
            _LOGGER.error("Error occurred during unlock: %s", err)

    async def async_lock(self, **kwargs) -> None:
        """Reset lock state manually."""
        self._attr_is_locked = True
        self.async_write_ha_state()
