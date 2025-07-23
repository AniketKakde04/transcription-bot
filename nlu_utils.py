import os
import json
import google.generativeai as genai

# Configure the generative AI model with your API key from the .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# This is the "brain" of our NLU. It's a detailed instruction for the LLM.
SYSTEM_PROMPT = """
You are an expert NLU (Natural Language Understanding) system for a loan recovery chatbot.
Your task is to analyze the user's message and determine their intent and any entities.

The possible intents are:
- get_customer_list
- get_customer_history
- get_due_amount
- get_payment_record
- greet
- goodbye
- unknown

The only entity to extract is 'account_number'.

Analyze the user's message and respond ONLY with a JSON object in the following format:
{"intent": "intent_name", "account_number": "extracted_account_number_or_null"}

Example user messages and their expected JSON output:
- "Show me my customers" -> {"intent": "get_customer_list", "account_number": null}
- "tell me about acc001" -> {"intent": "get_customer_history", "account_number": "ACC001"}
- "what is the due amount?" -> {"intent": "get_due_amount", "account_number": null}
- "thanks bye" -> {"intent": "goodbye", "account_number": null}
- "what is the weather" -> {"intent": "unknown", "account_number": null}
"""

def get_intent_and_entities(message):
    """
    Uses the Gemini LLM to determine the user's intent and extract entities.
    """
    try:
        # Combine the system prompt with the user's actual message
        full_prompt = f"{SYSTEM_PROMPT}\nUser message: \"{message}\""
        
        # Send the prompt to the model
        response = model.generate_content(full_prompt)
        
        # Clean up the response to get a valid JSON string
        json_response_str = response.text.strip().replace('```json', '').replace('```', '')
        
        # Parse the JSON string into a Python dictionary
        result = json.loads(json_response_str)
        
        intent = result.get("intent", "unknown")
        account_number = result.get("account_number")
        
        return intent, account_number

    except Exception as e:
        print(f"LLM NLU Error: {e}")
        # Fallback in case of an error, for example, if the API key is invalid
        return "unknown", None