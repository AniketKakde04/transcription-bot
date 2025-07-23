import os
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

# Import your existing and new utils
from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio
from sensitive_utils.detector import detect_and_encrypt_sensitive
from db_utils import get_agent_and_customers, get_customer_history
from nlu_utils import get_intent_and_entities

load_dotenv()
app = Flask(__name__)

# A dictionary to hold the conversation state for each user
conversation_state = {}

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    print("\n--- NEW REQUEST RECEIVED ---")
    resp = MessagingResponse()
    from_number = request.form.get("From")
    print(f"From Number: {from_number}")

    # Get the current context for this user, or create a new one
    user_context = conversation_state.get(from_number, {})

    if int(request.form.get("NumMedia", 0)) > 0:
        # --- Voice Note Logic ---
        print("Action: Processing Voice Note")
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
            print("-> Reply: Sent voice transcription.")
        except Exception as e:
            print(f"!!-- Voice Note Error: {e} --!!")
            resp.message("Sorry, I could not process your voice note.")
            
    else:
        # --- Text Message Logic with Debugging ---
        incoming_msg = request.form.get("Body", "").strip()
        print(f"Incoming Message: '{incoming_msg}'")
        
        # 1. Get intent and entities from NLU
        intent, account_number = get_intent_and_entities(incoming_msg)
        print(f"NLU Result -> Intent: {intent}, Account Number: {account_number}")

        if account_number:
            user_context['last_account_viewed'] = account_number
            print(f"Context updated: last_account_viewed = {account_number}")
        
        # 2. Route based on intent
        if intent == 'get_customer_list':
            print("Action: Executing 'get_customer_list'")
            agent, customers = get_agent_and_customers(from_number)
            if agent and customers:
                reply_msg = f"Hi {agent['agent_name']}. Here is your customer list:\n\n"
                for customer in customers:
                    reply_msg += f"👤 {customer['customer_name']} (#{customer['account_number']})\n"
                resp.message(reply_msg)
                print("-> Reply: Sent customer list.")
            else:
                resp.message("You have no customers assigned, or your number is not registered as an agent.")
                print("-> Reply: No customers or agent not registered.")

        elif intent == 'get_customer_history':
            print("Action: Executing 'get_customer_history'")
            acc_num_to_check = account_number or user_context.get('last_account_viewed')
            if acc_num_to_check:
                details = get_customer_history(acc_num_to_check, from_number)
                if details:
                    user_context['last_account_viewed'] = acc_num_to_check
                    reply_msg = f"📜 Account History for {details['customer_name']} ({acc_num_to_check}):\n\n"
                    reply_msg += f"💰 Total Loan: {details['total_loan']}\n"
                    reply_msg += f"💵 Due Amount: {details['due_amount']}\n"
                    reply_msg += f"🗓 EMIs Paid: {details['emis_paid']}\n"
                    reply_msg += f"📅 Last Payment: {details['last_payment_date']}\n"
                    reply_msg += f"📍 Location: {details['location']}\n"
                    reply_msg += f"📈 Record: {details['payment_record']}"
                    resp.message(reply_msg)
                    print(f"-> Reply: Sent history for {acc_num_to_check}.")
                else:
                    resp.message(f"Sorry, you do not have permission to view account number: {acc_num_to_check}")
                    print(f"-> Reply: No permission for {acc_num_to_check}.")
            else:
                resp.message("Of course. Please tell me which account number you'd like to see the history for.")
                print("-> Reply: Asking for account number.")
        
        elif intent in ['get_due_amount', 'get_payment_record']:
            print(f"Action: Executing '{intent}'")
            last_account = user_context.get('last_account_viewed')
            if last_account:
                details = get_customer_history(last_account, from_number)
                if details:
                    if intent == 'get_due_amount':
                        resp.message(f"The due amount for {last_account} is {details['due_amount']}.")
                        print(f"-> Reply: Sent due amount for {last_account}.")
                    elif intent == 'get_payment_record':
                        resp.message(f"The payment record for {last_account} is: {details['payment_record']}.")
                        print(f"-> Reply: Sent payment record for {last_account}.")
                else:
                    resp.message(f"Sorry, you do not have permission to view details for account {last_account}.")
                    print(f"-> Reply: No permission for follow-up on {last_account}.")
            else:
                resp.message("Sorry, I'm not sure which account you're asking about. Please specify an account number first.")
                print("-> Reply: Asking for account number (context missing).")

        elif intent == 'greet':
            print("Action: Executing 'greet'")
            resp.message("Hello! How can I help you today?")
            print("-> Reply: Sent greeting.")
        elif intent == 'goodbye':
            print("Action: Executing 'goodbye'")
            resp.message("You're welcome! Have a great day.")
            print("-> Reply: Sent goodbye message.")
        else:
            print("Action: No intent matched. Sending fallback message.")
            resp.message("Sorry, I'm not sure how to help with that. You can ask for your 'customer list' or for 'history of ACC...'.")

    # Save context and send response
    conversation_state[from_number] = user_context
    print(f"Final Response Object: {str(resp)}")
    print("--- REQUEST COMPLETE ---")
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)