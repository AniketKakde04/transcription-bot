import os
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

# Import all of your utility functions
from twilio_utils import download_audio_file
from transcription_utils import transcribe_audio
from sensitive_utils.detector import detect_and_encrypt_sensitive
from db_utils import get_agent_and_customers, get_customer_history, get_full_case_details,log_agent_notes,get_all_data_for_agent
from nlu_utils import get_intent_and_entities
from llm_utils import generate_priority_plan, generate_summary_for_supervisor

load_dotenv()
app = Flask(__name__)

# A dictionary to hold the conversation state for each user
conversation_state = {}

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    from_number = request.form.get("From")

    # Get the current context for this user, or create a new one
    user_context = conversation_state.get(from_number, {})

    if int(request.form.get("NumMedia", 0)) > 0:
        # --- Voice Note Logic ---
        media_url = request.form.get("MediaUrl  0")
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
        # --- Text Message Logic ---
        incoming_msg = request.form.get("Body", "").strip()
        
        # Get intent and entities from our NLU utility
        intent, account_number = get_intent_and_entities(incoming_msg)

        # If a new account number is mentioned, update the context
        if account_number:
            user_context['last_account_viewed'] = account_number
        
        # --- Intent Routing ---
        if intent == 'get_customer_list':
            agent, customers = get_agent_and_customers(from_number)
            if agent and customers:
                reply_msg = f"Hi {agent['agent_name']}. Here is your customer list:\n\n"
                for customer in customers:
                    reply_msg += f"👤 {customer['customer_name']} (#{customer['account_number']})\n"
                resp.message(reply_msg)
            else:
                resp.message("You have no customers assigned, or your number is not registered as an agent.")

        elif intent == 'get_customer_history':
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
                else:
                    resp.message(f"Sorry, you do not have permission to view account number: {acc_num_to_check}")
            else:
                resp.message("Of course. Please tell me which account number you'd like to see the history for.")

        elif intent == 'log_reason':
            try:
                notes = incoming_msg.split(':', 1)[1].strip()
            except IndexError:
                notes = ""

            if account_number and notes:
                success = log_agent_notes(account_number, from_number, notes)
                if success:
                    resp.message(f"Successfully logged notes for {account_number}. The case is now pending supervisor review.")
                else:
                    resp.message(f"Sorry, you do not have permission to log notes for account {account_number}.")
            else:
                resp.message("To log a reason, please use the format: log for <account_number>: <reason>")
        
        elif intent == 'get_priority_plan':
            all_data = get_all_data_for_agent(from_number)
            priority_plan = generate_priority_plan(all_data)
            resp.message(priority_plan)

        elif intent == 'get_summary':
            if account_number:
                # Note: Using from_number as supervisor_number for testing purposes
                details = get_full_case_details(account_number, from_number) 
                if details:
                    summary = generate_summary_for_supervisor(details)
                    resp.message(summary)
                else:
                    resp.message(f"Could not generate summary. You may not have permission to view {account_number}.")
            else:
                resp.message("Please specify an account number to summarize. Usage: summary <account_number>")

        elif intent in ['get_due_amount', 'get_payment_record']:
            last_account = user_context.get('last_account_viewed')
            if last_account:
                details = get_customer_history(last_account, from_number)
                if details:
                    if intent == 'get_due_amount':
                        resp.message(f"The due amount for {last_account} is {details['due_amount']}.")
                    elif intent == 'get_payment_record':
                        resp.message(f"The payment record for {last_account} is: {details['payment_record']}.")
                else:
                    resp.message(f"Sorry, you do not have permission to view details for account {last_account}.")
            else:
                resp.message("Sorry, I'm not sure which account you're asking about. Please specify an account number first.")

        elif intent == 'greet':
            resp.message("Hello! How can I help you today? You can ask for your 'customer list', a 'priority plan', or the 'history of an account'.")

        elif intent == 'goodbye':
            resp.message("You're welcome! Have a great day.")

        else:
            resp.message("Sorry, I'm not sure how to help with that. You can ask for help to see the available commands.")

    # Save the updated context for the user
    conversation_state[from_number] = user_context
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)