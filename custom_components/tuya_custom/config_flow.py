"""Config flow for Tuya Custom integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ENDPOINT,
    CONF_DEVICE_ID,
    DEFAULT_ENDPOINT,
)

ENDPOINTS = [
    {"label": "Western America (us)", "value": "https://openapi.tuyaus.com"},
    {"label": "Eastern America (ue)", "value": "https://openapi-ueaz.tuyaus.com"},
    {"label": "Central Europe (eu)", "value": "https://openapi.tuyaeu.com"},
    {"label": "Western Europe (we)", "value": "https://openapi-weaz.tuyaeu.com"},
    {"label": "China (cn)", "value": "https://openapi.tuyacn.com"},
]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_ENDPOINT, default=DEFAULT_ENDPOINT): SelectSelector(
            SelectSelectorConfig(
                options=ENDPOINTS,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_DEVICE_ID): str,
    }
)


class TuyaCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya Custom."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Tuya Lock ({user_input[CONF_DEVICE_ID][-4:]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )


