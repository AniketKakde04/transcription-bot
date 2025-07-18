import requests
import os

def download_audio_file(audio_url: str) -> bytes:
    auth = (os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    response = requests.get(audio_url, auth=auth)
    response.raise_for_status()
    return response.content