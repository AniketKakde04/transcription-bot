import os
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from googletrans import Translator

# Import your existing and new utils
from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio
from sensitive_utils.detector import detect_and_encrypt_sensitive # Or your NER detector
from db_utils import get_customers_by_agent

load_dotenv()
app = Flask(__name__)
translator = Translator()

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    
    # Get the sender's WhatsApp number from the incoming request
    from_number = request.form.get("From")
    print(f"Received message from: {from_number}")
    
    # --- Check if it's a VOICE NOTE or a TEXT MESSAGE ---
    if int(request.form.get("NumMedia", 0)) > 0:
        # --- This is a VOICE NOTE - Use existing transcription logic ---
        media_url = request.form.get("MediaUrl0")
        try:
            audio_data = download_audio_file(media_url)
            temp_audio_path = "temp_voice_note.ogg"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_data)

            # Here you can decide if you want to translate the audio to English
            # by setting task="translate" in your transcription function.
            transcribed_text = transcribe_audio(temp_audio_path)
            masked_text = detect_and_encrypt_sensitive(transcribed_text)
            resp.message(f"🗣 Transcribed text:\n\n{masked_text}")
            os.remove(temp_audio_path)
        except Exception as e:
            print("Error processing voice note:", e)
            resp.message("Sorry, I could not process your voice note.")
            
    else:
        # --- This is a TEXT MESSAGE - Use new Loan Recovery logic ---
        incoming_msg = request.form.get("Body", "").lower()
        
        # Translate the message to English to understand the command
        translated_msg = translator.translate(incoming_msg, dest='en').text.lower()
        
        # Check for specific commands
        if 'customer' in translated_msg or 'list' in translated_msg:
            # Fetch customers from the database for the agent who sent the message
            customers = get_customers_by_agent(from_number)
            
            if customers:
                reply_msg = "Here is your customer list:\n\n"
                for customer in customers:
                    reply_msg += f"👤 Name: {customer['customer_name']}\n"
                    reply_msg += f"   💰 Due: {customer['due_amount']}\n"
                    reply_msg += f"   #️⃣ Acc: {customer['account_number']}\n"
                    reply_msg += f"   📍 Loc: {customer['location']}\n\n"
                resp.message(reply_msg)
            else:
                resp.message("You have no customers assigned, or your number is not registered as an agent.")
        else:
            resp.message("Sorry, I don't understand that command. Please send a voice note for transcription or ask for your 'customer list'.")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)