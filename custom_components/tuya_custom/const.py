"""Constants for the Tuya Cloud Custom integration."""

DOMAIN = "tuya_custom"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_ENDPOINT = "endpoint"
CONF_DEVICE_ID = "device_id"

DEFAULT_ENDPOINT = "https://openapi.tuyaus.com"

# Common Tuya API Error Codes & Hints
TUYA_ERROR_HINTS = {
    1106: (
        "Permission Denied: Check if 'Smart Lock Core' service is subscribed "
        "under Cloud > API Services on Tuya IoT Platform."
    ),
    28841101: (
        "API service not subscribed: Subscribe to Smart Lock / Door Lock service."
    ),
    1010: "Token invalid or expired: Re-fetch a fresh access token.",
    1004: "Signature verification failed: Check CLIENT_SECRET or endpoint URL.",
}