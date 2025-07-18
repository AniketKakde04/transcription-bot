import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio

load_dotenv()
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    num_media = int(request.form.get("NumMedia", 0))
    resp = MessagingResponse()

    if num_media == 0:
        resp.message("Please send a voice message in any Indian language.")
        return str(resp)

    media_url = request.form.get("MediaUrl0")
    media_content_type = request.form.get("MediaContentType0", "")

    if not any(fmt in media_content_type for fmt in ["audio", "mp3", "wav", "ogg"]):
        resp.message("Unsupported audio format. Please send MP3, WAV or OGG voice note.")
        return str(resp)

    try:
        # Step 1: Download audio as bytes
        audio_data = download_audio_file(media_url)

        # Step 2: Save bytes to a temporary file
        temp_audio_path = "temp_voice_note.ogg"  # You may want to generate a unique name
        with open(temp_audio_path, "wb") as f:
            f.write(audio_data)

        # Step 3: Transcribe using Whisper
        transcribed_text = transcribe_audio(temp_audio_path)

        # Step 4: Reply with transcription
        resp.message(f"🗣 Transcribed text:\n\n{transcribed_text}")

        # Clean up temp file
        os.remove(temp_audio_path)
    except Exception as e:
        print("Error:", e)
        resp.message("Sorry, could not process your voice note. Try again.")

    return str(resp)

