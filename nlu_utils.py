import os
import json
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

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
- log_reason
- greet
- goodbye
- unknown

The only entity to extract is 'account_number'.

Analyze the user's message and respond ONLY with a JSON object in the following format:
{"intent": "intent_name", "account_number": "extracted_account_number_or_null"}

Example user messages and their expected JSON output:
- "who should I call first?" -> {"intent": "get_priority_plan", "account_number": null}
- "Show me my customers" -> {"intent": "get_customer_list", "account_number": null}
- "tell me about acc001" -> {"intent": "get_customer_history", "account_number": "ACC001"}
- "log for acc002: customer has lost their job" -> {"intent": "log_reason", "account_number": "ACC002"}
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