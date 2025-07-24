import os
import json
import google.generativeai as genai

# (genai configuration remains the same)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# In nlu_utils.py

SYSTEM_PROMPT = """
You are an expert NLU (Natural Language Understanding) system for a loan recovery chatbot.
Your task is to analyze the user's message and determine their intent and any entities.

The possible intents are:
- get_summary
- get_priority_plan
- get_customer_list
- get_customer_history
- get_due_amount
- get_payment_record
- log_reason
- greet
- goodbye
- unknown

The only entity to extract is 'account_number'.

Analyze the user's message and respond ONLY with a JSON object in the following format:
{"intent": "intent_name", "account_number": "extracted_account_number_or_null"}

Example user messages and their expected JSON output:
- "summarize acc001 for my supervisor" -> {"intent": "get_summary", "account_number": "ACC001"}
- "who should I call first?" -> {"intent": "get_priority_plan", "account_number": null}
- "Show me my customers" -> {"intent": "get_customer_list", "account_number": null}
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

