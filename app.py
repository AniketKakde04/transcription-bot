
import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio
from masking_utils import load_patterns, mask_sensitive

import nltk
nltk.download('punkt')  # Ensure 'punkt' is downloaded at runtime

from sensitive_utils.detector import detect_and_encrypt_sensitive

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

        # Step 4: Detect and encrypt sensitive info
        masked_text = detect_and_encrypt_sensitive(transcribed_text)

        # Step 5: Reply with masked transcription
        resp.message(f"🗣 Transcribed text:\n\n{masked_text}")

        # Clean up temp file
        os.remove(temp_audio_path)
    except Exception as e:
        print("Error:", e)
        resp.message("Sorry, could not process your voice note. Try again.")

    return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

