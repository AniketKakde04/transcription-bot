import os
import json
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# NEW: Simplified 'log_reason' and added 'provide_notes' intent
SYSTEM_PROMPT = """
You are an expert NLU (Natural Language Understanding) system for a loan recovery chatbot.
Your task is to analyze the user's message and determine their intent and any entities.

The possible intents are:
- get_priority_plan
- get_customer_list
- get_customer_history
- log_reason
- provide_notes
- greet
- goodbye
- unknown

The only entity to extract is 'account_number'.

CRITICAL INSTRUCTION: If the user message seems to be a simple statement of fact (like a reason for non-payment) and not a direct command, classify the intent as 'provide_notes'.

Analyze the user's message and respond ONLY with a JSON object in the following format:
{"intent": "intent_name", "account_number": "extracted_account_number_or_null"}

Example user messages and their expected JSON output:
- "I need to log a reason for acc001" -> {"intent": "log_reason", "account_number": "ACC001"}
- "The customer has lost their job" -> {"intent": "provide_notes", "account_number": null}
- "who should I call first?" -> {"intent": "get_priority_plan", "account_number": null}
"""

def get_intent_and_entities(message):
    """
    Uses the Gemini LLM to determine the user's intent and extract entities.
    """
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