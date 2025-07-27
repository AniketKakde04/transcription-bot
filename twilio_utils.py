import requests
import os

def download_audio_file(audio_url: str) -> bytes:
    auth = (os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    response = requests.get(audio_url, auth=auth)
    response.raise_for_status()
    return response.content

# In twilio_utils.py
from twilio.rest import Client

def send_whatsapp_message(to_number, body):
    """
    Sends a proactive WhatsApp message to a specified number.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = 'whatsapp:+14155238886' # Your Twilio Sandbox Number

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            from_=twilio_number,
            body=body,
            to=to_number
        )
        print(f"Notification sent successfully to {to_number}, SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp notification: {e}")
        return False