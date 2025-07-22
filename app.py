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
from db_utils import get_agent_and_customers, get_customer_history

load_dotenv()
app = Flask(__name__)
translator = Translator()

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    from_number = request.form.get("From")

    if int(request.form.get("NumMedia", 0)) > 0:
        # --- Handle voice note ---
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
        # --- Handle text message ---
        incoming_msg = request.form.get("Body", "").strip()
        command_parts = incoming_msg.split()
        command = command_parts[0].lower() if command_parts else ""

        # --- List customers ---
        if command == "list" or command == "customer":
            agent, customers = get_agent_and_customers(from_number)
            if agent and customers:
                reply_msg = f"Hi {agent['agent_name']}. This is your customer list:\n\n"
                for customer in customers:
                    reply_msg += f"👤 {customer['customer_name']} (#{customer['account_number']})\n"
                resp.message(reply_msg)
            else:
                resp.message("You have no customers assigned, or your number is not registered as an agent.")

        # --- Customer history ---
        elif command == "history":
            if len(command_parts) > 1:
                account_number = command_parts[1].upper()
                details = get_customer_history(account_number)
                if details:
                    reply_msg = f"📜 Account History for {details['customer_name']} ({account_number}):\n\n"
                    reply_msg += f"💰 Total Loan: {details['total_loan']}\n"
                    reply_msg += f"💵 Due Amount: {details['due_amount']}\n"
                    reply_msg += f"🗓 EMIs Paid: {details['emis_paid']}\n"
                    reply_msg += f"📅 Last Payment: {details['last_payment_date']}\n"
                    reply_msg += f"📍 Location: {details['location']}\n"
                    reply_msg += f"📈 Record: {details['payment_record']}"
                    resp.message(reply_msg)
                else:
                    resp.message(f"Sorry, no history found for account number: {account_number}")
            else:
                resp.message("Please provide an account number. Usage: history <account_number>")

        # --- Unknown command ---
        else:
            resp.message("Sorry, I don't understand. Send 'list' for customers or 'history <account_number>' for details.")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
