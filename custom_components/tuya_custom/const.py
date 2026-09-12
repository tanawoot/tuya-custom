"""Constants for the Tuya Custom integration."""

DOMAIN = "tuya_custom"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_ENDPOINT = "endpoint"
CONF_DEVICE_ID = "device_id"

DEFAULT_ENDPOINT = "https://openapi.tuyaeu.com"

TUYA_ERROR_HINTS = {
    28841101: (
        "API service not subscribed: Go to Tuya IoT Platform > Cloud > "
        "Your Project > Service API, and subscribe to Smart Lock / Door Lock service."
    ),
    1010: "Token invalid or expired: Re-fetch a fresh access token.",
    1004: "Signature verification failed: Check CLIENT_SECRET, endpoint URL, or string-to-sign structure.",
}