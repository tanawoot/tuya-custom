
# Tuya Custom
Integration for Home Assistant

A custom Home Assistant integration designed to control Tuya-based smart door locks using Tuya Open API v2 password-free remote unlocking mechanism.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

---

## Features

* **Password-Free Remote Unlock**: Triggers direct remote unlocking via Tuya password-free ticket APIs.
* **Auto-Reset UI State**: Automatically updates the entity state to `Unlocked` upon success and resets back to `Locked` after 5 seconds for smooth UI interaction.
* **UI Config Flow**: Native setup wizard—no manual YAML edits required.
* **Asynchronous Execution**: Native non-blocking HTTP requests via `aiohttp`.
* **Diagnostic Hints**: Built-in error code mapping for common Tuya API integration issues.

---

## Directory Structure

```text
tuya-custom/
├── .gitignore
├── hacs.json
├── README.md
└── custom_components/
    └── tuya_custom/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── lock.py
        ├── manifest.json
        ├── strings.json
        ├── icon.png
        └── logo.png

```

---

## Installation via HACS

1. Open **Home Assistant** and navigate to **HACS**.
2. Click the three dots `⋮` in the top-right corner and select **Custom repositories**.
3. Add the repository URL:
```text
[https://github.com/tanawoot/tuya-custom](https://github.com/tanawoot/tuya-custom)

```


4. Set **Category** to `Integration` and click **Add**.
5. Search for `Tuya Custom` and click **Download**.
6. **Restart Home Assistant**.

---

## Configuration

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Tuya Custom**.
3. Fill in your Tuya Cloud Platform credentials:

| Field | Description |
| --- | --- |
| **Client ID** | Access Key from your Tuya Cloud Project |
| **Client Secret** | Secret Key from your Tuya Cloud Project |
| **Endpoint** | Server region URL (e.g., `https://openapi.tuyaeu.com`) |
| **Device ID** | Target Tuya smart door lock ID |

---

## API Endpoints Used

This integration utilizes the following Tuya Open API v2 endpoints:

1. **Request Password Ticket:**
`POST /v1.0/devices/{device_id}/door-lock/password-ticket`
2. **Password-Free Remote Unlock:**
`POST /v1.0/devices/{device_id}/door-lock/password-free/open-door`

---

## Troubleshooting

### Error: `clientId is invalid` (Code 2009)

* Verify that the selected **Endpoint** region matches your Tuya Cloud Project region.
* Delete the integration, restart Home Assistant, and add it again while ensuring no leading or trailing whitespace exists in your credentials.

---

## Security Warning

Never commit actual API keys, Client Secrets, or Personal Access Tokens into this repository. All credentials should strictly be configured via the Home Assistant UI Config Flow.

---

## License

MIT License

```

<FollowUp label="Would you like me to inspect or optimize any other files in the repo?" query="Please inspect and optimize const.py and config_flow.py in the tuya-custom repository."/>

```