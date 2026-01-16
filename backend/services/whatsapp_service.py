import requests # type: ignore
from django.conf import settings # type: ignore


def send_whatsapp_reminder(phone_number, template_name, variables):
    """
    Send WhatsApp message using Whatomate
    """
    url = f"{settings.WHATOMATE_BASE_URL}/send-template"

    payload = {
        "to": phone_number,
        "template_name": template_name,
        "variables": variables,
        "sender_id": settings.WHATOMATE_SENDER_ID,
    }

    headers = {
        "Authorization": f"Bearer {settings.WHATOMATE_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)

    response.raise_for_status()
    return response.json()
