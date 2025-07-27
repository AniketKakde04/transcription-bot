import os
import json
import google.generativeai as genai

# I've updated the model name back to the standard one for this task
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# --- THIS IS THE KEY FIX: A more robust and complete prompt for the NLU ---
SYSTEM_PROMPT = """
You are an expert NLU (Natural Language Understanding) system for a loan recovery chatbot.
Your task is to analyze the user's message and determine their intent and any entities.

The possible intents are:
- get_priority_plan
- get_customer_list
- get_customer_history
- get_due_amount
- get_payment_record
- get_summary
- send_report
- get_pending_reports
- submit_decision
- log_reason
- greet
- goodbye
- unknown

The only entity to extract is 'account_number'.

CRITICAL INSTRUCTION: Differentiate between 'get_customer_history' and 'get_summary'.
- 'get_customer_history' is for the agent's own use (e.g., "show me the history").
- 'get_summary' is a specific request for the supervisor-level summary (e.g., "summarize this for my boss").

Analyze the user's message and respond ONLY with a JSON object in the following format:
{"intent": "intent_name", "account_number": "extracted_account_number_or_null"}

Example user messages and their expected JSON output:
- "summarize acc001" -> {"intent": "get_summary", "account_number": "ACC001"}
- "give me a summary for acc002" -> {"intent": "get_summary", "account_number": "ACC002"}
- "tell me about acc001" -> {"intent": "get_customer_history", "account_number": "ACC001"}
- "what is the history for acc002" -> {"intent": "get_customer_history", "account_number": "ACC002"}
- "who should I call first?" -> {"intent": "get_priority_plan", "account_number": null}
- "log for acc002: customer has lost their job" -> {"intent": "log_reason", "account_number": "ACC002"}
- "show me pending reports" -> {"intent": "get_pending_reports", "account_number": null}
- "decision for acc001: offer a one month extension" -> {"intent": "submit_decision", "account_number": "ACC001"}
- "send this report to my supervisor" -> {"intent": "send_report", "account_number": null}
"""

def get_intent_and_entities(message):
    try:
        full_prompt = f"{SYSTEM_PROMPT}\nUser message: \"{message}\""
        response = model.generate_content(full_prompt)
        json_response_str = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(json_response_str)
        
        intent = result.get("intent", "unknown")
        account_number = result.get("account_number")
        
        return intent, account_number
    except Exception as e:
        print(f"LLM NLU Error: {e}")
        return "unknown", None