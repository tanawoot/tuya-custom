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
        self._unlock_duration = 10  # Unlock duration in seconds

        self._attr_name = "Door Lock"
        self._attr_unique_id = f"tuya_custom_lock_{self._device_id}"
        self._attr_is_locked = True
        self._attr_icon = "mdi:lock"

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

    async def _async_send_device_commands(self, session, token, commands):
        """Send direct device control commands via Tuya DP."""
        path = f"/v1.0/devices/{self._device_id}/commands"
        payload = {"commands": commands}
        return await self._async_send_tuya_request(
            session, "POST", path, body_dict=payload, token=token
        )

    async def async_unlock(self, **kwargs) -> None:
        """Unlock the door and temporarily disable auto lock for the specified duration."""
        _LOGGER.info("Executing hold-open unlock sequence for %s seconds...", self._unlock_duration)
        session = async_get_clientsession(self.hass)

        try:
            token = await self._async_get_access_token(session)

            # 1. Disable Auto Lock DP commands to keep physical lock open
            disable_autolock_cmd = [
                {"code": "automatic_lock", "value": False},
                {"code": "auto_lock", "value": False},
            ]
            await self._async_send_device_commands(session, token, disable_autolock_cmd)

            # 2. Request password ticket
            ticket_path = f"/v1.0/devices/{self._device_id}/door-lock/password-ticket"
            ticket_res = await self._async_send_tuya_request(session, "POST", ticket_path, token=token)

            if not ticket_res.get("success"):
                _LOGGER.error("Failed to obtain ticket: %s%s", ticket_res, _error_hint(ticket_res))
                return

            ticket_id = ticket_res["result"]["ticket_id"]

            # 3. Send password-free open door request
            unlock_path = f"/v1.0/devices/{self._device_id}/door-lock/password-free/open-door"
            payload = {"ticket_id": ticket_id}
            unlock_res = await self._async_send_tuya_request(
                session, "POST", unlock_path, body_dict=payload, token=token
            )

            if unlock_res.get("success"):
                _LOGGER.info("Door unlocked successfully. Entering hold-open period.")
                self._attr_is_locked = False
                self.async_write_ha_state()

                # 4. Wait for the specified duration without looping API calls
                await asyncio.sleep(self._unlock_duration)

                # 5. Restore Auto Lock and trigger physical lock command
                _LOGGER.info("Hold-open time expired. Restoring Auto Lock and relocking.")
                enable_autolock_cmd = [
                    {"code": "automatic_lock", "value": True},
                    {"code": "auto_lock", "value": True},
                    {"code": "lock", "value": True},
                ]
                await self._async_send_device_commands(session, token, enable_autolock_cmd)

            else:
                _LOGGER.error("Failed to unlock door: %s%s", unlock_res, _error_hint(unlock_res))

        except Exception as err:
            _LOGGER.error("Error occurred during unlock sequence: %s", err)
        finally:
            # Always sync UI state back to locked
            self._attr_is_locked = True
            self.async_write_ha_state()

    async def async_lock(self, **kwargs) -> None:
        """Manually lock the door and ensure Auto Lock is enabled."""
        session = async_get_clientsession(self.hass)
        try:
            token = await self._async_get_access_token(session)

            # Re-enable Auto Lock and execute lock command
            enable_autolock_cmd = [
                {"code": "automatic_lock", "value": True},
                {"code": "auto_lock", "value": True},
                {"code": "lock", "value": True},
            ]
            await self._async_send_device_commands(session, token, enable_autolock_cmd)
        except Exception as err:
            _LOGGER.error("Error during manual lock execution: %s", err)

        self._attr_is_locked = True
        self.async_write_ha_state()