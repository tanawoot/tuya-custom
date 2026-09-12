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

# รายชื่อ Data Center Endpoints ของ Tuya
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