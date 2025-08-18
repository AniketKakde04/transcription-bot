import os
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from db_utils import get_data_for_prediction
from prediction_utils import make_prediction
from db_utils import get_triage_details,save_ai_decision
from llm_utils import generate_ai_decision

# Import all of your utility functions
from twilio_utils import download_audio_file, send_whatsapp_message
from prediction_utils import make_prediction, generate_model_based_plan
from transcription_utils import transcribe_audio
from sensitive_utils.detector import detect_and_encrypt_sensitive
from db_utils import get_agent_and_customers, get_customer_history, log_agent_notes, get_all_data_for_agent, create_communication_record, get_pending_reports_for_supervisor, submit_supervisor_decision
from nlu_utils import get_intent_and_entities
from llm_utils import generate_priority_plan, generate_summary_for_supervisor

load_dotenv()
app = Flask(__name__)
conversation_state = {}

# --- Central function to process all text-based commands ---
def process_text_message(incoming_msg, from_number):
    """
    This function contains all the logic to handle intents and generate replies.
    It can be called with text from either a voice note or a typed message.
    """
    resp = MessagingResponse()
    user_context = conversation_state.get(from_number, {})

    # 1. Get intent and entities from our NLU utility
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
            resp.message("You have no customers assigned.")

    elif intent == 'get_customer_history':
        acc_num_to_check = account_number or user_context.get('last_account_viewed')
        if acc_num_to_check:
            details = get_customer_history(acc_num_to_check, from_number)
            if details:
                user_context['last_account_viewed'] = acc_num_to_check
                reply_msg = f"📜 Account History for {details['customer_name']} ({acc_num_to_check}):\n"
                reply_msg += f"💰 Total Loan: {details['total_loan']}\n"
                reply_msg += f"💵 Due Amount: {details['due_amount']}\n"
                reply_msg += f"🗓 EMIs Paid: {details['emis_paid']}\n"
                reply_msg += f"📈 Record: {details['payment_record']}"
                resp.message(reply_msg)
            else:
                resp.message(f"Sorry, you don't have permission to view {acc_num_to_check}.")
        else:
            resp.message("Which account number would you like to see?")
    
    # In app.py's process_text_message function

    # In app.py's process_text_message function

    elif intent == 'log_reason':
            try:
                notes = incoming_msg.split(':', 1)[1].strip()
            except IndexError:
                notes = ""

            if account_number and notes:
                # First, log the agent's notes
                success = log_agent_notes(account_number, from_number, notes)
                
                if success:
                    # After logging, get the data and make a prediction
                    prediction_data = get_data_for_prediction(account_number)
                    prediction_result = make_prediction(prediction_data)

                    reply_msg = (
                        f"Successfully logged notes for {account_number}.\n\n"
                        f"🤖 **Automated Analysis:**\n{prediction_result}"
                    )
                    resp.message(reply_msg)
                else:
                    resp.message(f"Sorry, you do not have permission to log notes for account {account_number}.")
            else:
                resp.message("To log a reason, please use the format: log for <account_number>: <reason>")

    elif intent == 'provide_notes':
            # This is the second step, where the user provides the notes
        if user_context.get('next_action') == 'awaiting_notes':
            acc_num_for_notes = user_context.get('action_account_number')
            notes = incoming_msg # The whole message is the note
                
            success = log_agent_notes(acc_num_for_notes, from_number, notes)
            if success:
                resp.message(f"Got it. I've logged your notes for {acc_num_for_notes}.")
                # Clear the next_action so the bot isn't stuck
                user_context.pop('next_action', None)
                user_context.pop('action_account_number', None)
            else:
                resp.message(f"Sorry, you do not have permission to log notes for account {acc_num_for_notes}.")
        else:
            resp.message("Sorry, I wasn't expecting any notes. What would you like to do?")

# ... (rest of your app.py file)
    

    elif intent == 'get_priority_plan':
            # 1. Get all the necessary feature data for the agent's customers
            all_data = get_all_data_for_agent(from_number)
            
            # 2. Generate the priority plan using the custom-trained model
            priority_plan = generate_model_based_plan(all_data)
            
            # 3. Send the plan to the agent
            resp.message(priority_plan)
        
    # In app.py's process_text_message function

    elif intent == 'send_report':
            # --- THIS IS THE KEY FIX ---
            # The bot now checks for an account number in the current message first,
            # and only falls back to its memory if one isn't provided.
            account_to_report = account_number or user_context.get('last_account_viewed')
            
            if account_to_report:
                # First, get the agent's own details to find their supervisor
                # This logic can be moved to db_utils.py for cleanliness in a future step
                conn = sqlite3.connect('loan_recovery.db')
                cursor = conn.cursor()
                cursor.execute("SELECT supervisor_number FROM agents WHERE whatsapp_number = ?", (from_number,))
                agent_info = cursor.fetchone()
                conn.close()
                
                if agent_info and agent_info[0]:
                    supervisor_number = agent_info[0]
                    
                    # Fetch the customer details to generate the summary
                    details = get_customer_history(account_to_report, from_number)
                    if details:
                        summary = generate_summary_for_supervisor(details)
                        
                        # Save the report to the communications table
                        success = create_communication_record(account_to_report, from_number, supervisor_number, summary)
                        
                        if success:
                            resp.message(f"Your report for {account_to_report} has been sent to your supervisor for review.")
                        else:
                            resp.message("Sorry, there was an error sending your report. Please try again.")
                    else:
                        resp.message(f"Could not find details for {account_to_report} to generate a report.")
                else:
                    resp.message("Could not find a supervisor assigned to you in the system.")
            else:
                resp.message("Sorry, I'm not sure which account you want to send a report for. Please specify an account number or view an account's history first.")

# ... (rest of your app.py file)

    elif intent == 'get_pending_reports':
        reports = get_pending_reports_for_supervisor(from_number)
        if reports:
            reply_msg = "Here are your pending reports:\n"
            for report in reports:
                reply_msg += f"\n--------------------\n"
                reply_msg += f"*Report ID:* {report['comm_id']}\n"
                reply_msg += f"*Account:* {report['account_number']}\n"
                reply_msg += f"*Summary:* {report['summary_report']}\n"
            resp.message(reply_msg)
        else:
            resp.message("You have no pending reports to review.")
            
    elif intent == 'submit_decision':
        try:
            parts = incoming_msg.split(':', 1)
            decision = parts[1].strip()
            comm_id_str = parts[0].split()[-1]
            comm_id = int(comm_id_str)
            agent_to_notify, acc_num = submit_supervisor_decision(comm_id, decision)
            if agent_to_notify:
                notification_body = f"Your supervisor has reviewed the case for *{acc_num}*.\n\n*Decision:* {decision}"
                send_whatsapp_message(agent_to_notify, notification_body)
                resp.message(f"Your decision for report ID {comm_id} has been recorded and the agent has been notified.")
            else:
                resp.message("Sorry, there was an error recording your decision.")
        except (IndexError, ValueError):
            resp.message("To submit a decision, use the format: decision for <report_id>: <your_decision>")

    else:
        resp.message("Sorry, I don't understand that command. Please try again.")

    conversation_state[from_number] = user_context
    return str(resp)


# In app.py

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get("From")

    if int(request.form.get("NumMedia", 0)) > 0:
        # --- This is a VOICE NOTE (In-Memory Processing) ---
        media_url = request.form.get("MediaUrl0")
        try:
            # 1. Download audio as bytes
            audio_data = download_audio_file(media_url)
            
            # 2. Transcribe the audio bytes directly from memory
            transcribed_text = transcribe_audio(audio_data)
            
            # 3. Process the transcribed text using our central function
            return process_text_message(transcribed_text, from_number)

        except Exception as e:
            print("Error processing voice note:", e)
            resp = MessagingResponse()
            resp.message("Sorry, I could not process your voice note.")
            return str(resp)
            
    else:
        # --- This is a TEXT MESSAGE ---
        incoming_msg = request.form.get("Body", "").strip()
        processed_text = detect_and_encrypt_sensitive(incoming_msg)
        # Process the typed text using our central function
        return process_text_message(processed_text, from_number)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)