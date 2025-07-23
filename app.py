import os
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio
from sensitive_utils.detector import detect_and_encrypt_sensitive
from db_utils import get_agent_and_customers, get_customer_history
from nlu_utils import get_intent_and_entities

load_dotenv()
app = Flask(__name__)

# --- NEW: A dictionary to hold the conversation state for each user ---
conversation_state = {}

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    from_number = request.form.get("From")

    # Get the current context for this user, or create a new one
    user_context = conversation_state.get(from_number, {})

    if int(request.form.get("NumMedia", 0)) > 0:
        # Voice Note Logic (no changes)
        # ...
        pass # Placeholder for your existing voice note code
            
    else:
        # --- Text Message Logic with Memory ---
        incoming_msg = request.form.get("Body", "").strip()
        intent, account_number = get_intent_and_entities(incoming_msg)

        # If an account number is mentioned, update the context
        if account_number:
            user_context['last_account_viewed'] = account_number
        
        # --- Intent Routing ---
        if intent == 'get_customer_list':
            # ... (no changes to this block)
            agent, customers = get_agent_and_customers(from_number)
            if agent and customers:
                reply_msg = f"Hi {agent['agent_name']}. Here is your customer list:\n\n"
                for customer in customers:
                    reply_msg += f"👤 {customer['customer_name']} (#{customer['account_number']})\n"
                resp.message(reply_msg)
            else:
                resp.message("You have no customers assigned, or your number is not registered as an agent.")


        # In app.py

        elif intent == 'get_customer_history':
            if account_number:
                # --- THIS IS THE KEY CHANGE ---
                # We now pass the agent's number (from_number) to the function
                details = get_customer_history(account_number, from_number)
                
                if details:
                    user_context['last_account_viewed'] = account_number
                    reply_msg = f"📜 Account History for {details['customer_name']} ({account_number}):\n\n"
                    reply_msg += f"💰 Total Loan: {details['total_loan']}\n"
                    reply_msg += f"💵 Due Amount: {details['due_amount']}\n"
                    reply_msg += f"🗓 EMIs Paid: {details['emis_paid']}\n"
                    reply_msg += f"📅 Last Payment: {details['last_payment_date']}\n"
                    reply_msg += f"📍 Location: {details['location']}\n"
                    reply_msg += f"📈 Record: {details['payment_record']}"
                    resp.message(reply_msg)
                else:
                    # The message is now more secure and accurate
                    resp.message(f"Sorry, you do not have permission to view account number: {account_number}")
            else:
                resp.message("Of course. Please tell me which account number you'd like to see the history for.")
        
        # --- NEW: Handle follow-up questions using context ---
        elif intent in ['get_due_amount', 'get_payment_record']:
            last_account = user_context.get('last_account_viewed')
            if last_account:
                details = get_customer_history(last_account)
                if intent == 'get_due_amount':
                    resp.message(f"The due amount for {last_account} is {details['due_amount']}.")
                elif intent == 'get_payment_record':
                    resp.message(f"The payment record for {last_account} is: {details['payment_record']}.")
            else:
                resp.message("Sorry, I'm not sure which account you're asking about. Please specify an account number first.")

        elif intent == 'greet':
            resp.message("Hello! How can I help you today?")
        elif intent == 'goodbye':
            resp.message("You're welcome! Have a great day.")
        else:
            resp.message("Sorry, I don't understand that. You can ask for your 'customer list' or 'history of ACC...'.")

    # Save the updated context for the user
    conversation_state[from_number] = user_context
    return str(resp)

# ... (if __name__ == "__main__": block remains the same)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)