import os
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from googletrans import Translator

# Import your existing and new utils
from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio
from sensitive_utils.detector import detect_and_encrypt_sensitive
from db_utils import get_agent_and_customers # <-- Use the new function

load_dotenv()
app = Flask(__name__)
translator = Translator()

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    from_number = request.form.get("From")
    
    if int(request.form.get("NumMedia", 0)) > 0:
        # (No changes needed in the voice note section)
        media_url = request.form.get("MediaUrl0")
        try:
            audio_data = download_audio_file(media_url)
            temp_audio_path = "temp_voice_note.ogg"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_data)
            transcribed_text = transcribe_audio(temp_audio_path)
            masked_text = detect_and_encrypt_sensitive(transcribed_text)
            resp.message(f"🗣 Transcribed text:\n\n{masked_text}")
            os.remove(temp_audio_path)
        except Exception as e:
            print("Error processing voice note:", e)
            resp.message("Sorry, I could not process your voice note.")
            
    else:
        # --- This is the TEXT MESSAGE logic ---
        incoming_msg = request.form.get("Body", "").lower()
        translated_msg = translator.translate(incoming_msg, dest='en').text.lower()
        
        if 'customer' in translated_msg or 'list' in translated_msg:
            # Fetch both agent and customers
            agent, customers = get_agent_and_customers(from_number)
            
            # Check if both the agent and their customers were found
            if agent and customers:
                # Create the new, personalized reply message
                reply_msg = f"Hi {agent['agent_name']}. This is your customer list:\n\n"
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