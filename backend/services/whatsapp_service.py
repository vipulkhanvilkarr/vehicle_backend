import requests
from django.conf import settings


def send_whatsapp_reminder(phone_number: str, message: str):
    """
    Send WhatsApp message using Whapi.Cloud
    """
    # Clean the phone number: remove spaces, dashes, and '+'
    clean_number = "".join(filter(str.isdigit, str(phone_number)))

    # If it's a 10-digit number, prepend 91 (India)
    if len(clean_number) == 10:
        clean_number = f"91{clean_number}"

    url = f"{settings.WHAPI_BASE_URL}/messages/text"

    headers = {
        "Authorization": f"Bearer {settings.WHAPI_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "to": clean_number,                # Now includes country code, e.g. 917588722435
        "body": message,
        "instance_id": settings.WHINSTANCE_ID if hasattr(settings, 'WHINSTANCE_ID') else settings.WHAPI_INSTANCE_ID,
    }

    print(f"--- [Whapi] Attempting to send message to: {clean_number} ---")
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    
    print(f"--- [Whapi] Response Status: {response.status_code} ---")
    print(f"--- [Whapi] Response Body: {response.text} ---")
    
    response.raise_for_status()
    return response.json()
