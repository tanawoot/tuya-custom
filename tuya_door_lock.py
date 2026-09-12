import hashlib
import hmac
import json
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables
CLIENT_ID = os.environ["TUYA_CLIENT_ID"]
CLIENT_SECRET = os.environ["TUYA_CLIENT_SECRET"]
ENDPOINT = os.environ.get("TUYA_ENDPOINT", "https://openapi.tuyaeu.com")
DEVICE_ID = os.environ["TUYA_DEVICE_ID"]

# Common Tuya API error codes and debugging hints
TUYA_ERROR_HINTS = {
    28841101: (
        "API service not subscribed: Go to Tuya IoT Platform > Cloud > "
        "Your Project > Service API, and subscribe to Smart Lock / Door Lock service."
    ),
    1010: "Token invalid or expired: Re-fetch a fresh access token.",
    1004: "Signature verification failed: Check CLIENT_SECRET, endpoint URL, or string-to-sign structure.",
}


def generate_sign(client_id, client_secret, access_token, t, method, path, body=""):
    """Calculate Tuya Open API v2 signature."""
    # 1. SHA256 hashing for request body (defaults to empty string hash if no body)
    content_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    
    # 2. String-to-sign pattern: HTTP Method + \n + Content-SHA256 + \n + Headers + \n + PathAndQuery
    # Note: Double \n is used when custom headers are omitted.
    string_to_sign = f"{method}\n{content_sha256}\n\n{path}"

    # 3. Concatenate all signature parameters
    sign_str = client_id + (access_token if access_token else "") + t + string_to_sign
    
    # 4. Generate HMAC-SHA256 signature string
    sign = (
        hmac.new(
            client_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        )
        .hexdigest()
        .upper()
    )
    return sign


def _error_hint(res):
    """Retrieve hint message for known Tuya API error codes."""
    hint = TUYA_ERROR_HINTS.get(res.get("code"))
    return f"\nHint: {hint}" if hint else ""


def get_access_token():
    """Fetch Access Token from Tuya Open API."""
    t = str(int(time.time() * 1000))
    path = "/v1.0/token?grant_type=1"
    sign = generate_sign(CLIENT_ID, CLIENT_SECRET, "", t, "GET", path)

    headers = {
        "client_id": CLIENT_ID,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256",
    }

    res = requests.get(ENDPOINT + path, headers=headers).json()
    if res.get("success"):
        return res["result"]["access_token"]
    raise Exception(f"Failed to get token: {res}{_error_hint(res)}")


def send_tuya_request(method, path, body_dict=None, token=None):
    """Send an authenticated HTTP request to Tuya API using signature and token."""
    if not token:
        token = get_access_token()

    t = str(int(time.time() * 1000))
    body_str = json.dumps(body_dict) if body_dict else ""

    sign = generate_sign(
        CLIENT_ID, CLIENT_SECRET, token, t, method, path, body_str
    )

    headers = {
        "client_id": CLIENT_ID,
        "access_token": token,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256",
        "Content-Type": "application/json",
    }

    url = ENDPOINT + path
    if method == "POST":
        res = requests.post(url, headers=headers, data=body_str)
    else:
        res = requests.get(url, headers=headers)

    return res.json()


def unlock_door():
    """Request ticket ID and perform password-free unlock action."""
    try:
        # Obtain access token once for the session
        token = get_access_token()

        # Step A: Request password ticket ID
        ticket_path = f"/v1.0/devices/{DEVICE_ID}/door-lock/password-ticket"
        ticket_res = send_tuya_request("POST", ticket_path, token=token)

        if not ticket_res.get("success"):
            print("Failed to obtain ticket:", ticket_res, _error_hint(ticket_res))
            return

        ticket_id = ticket_res["result"]["ticket_id"]
        print(f"Ticket ID obtained: {ticket_id}")

        # Step B: Trigger remote unlock with ticket ID
        unlock_path = f"/v1.0/devices/{DEVICE_ID}/door-lock/password-free/open-door"
        payload = {"ticket_id": ticket_id}

        unlock_res = send_tuya_request("POST", unlock_path, body_dict=payload, token=token)

        if unlock_res.get("success"):
            print("ปลดล็อกประตูเรียบร้อยแล้วค่ะพี่!")
        else:
            print("ปลดล็อกไม่สำเร็จ:", unlock_res, _error_hint(unlock_res))

    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    unlock_door()
    