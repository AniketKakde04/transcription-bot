import re
from deep_translator import GoogleTranslator

# Define keywords for each intent
INTENT_KEYWORDS = {
    'get_customer_list': ['list', 'customers', 'customer', 'accounts', 'users'],
    'get_customer_history': ['history', 'details', 'info', 'information', 'about'],
    'greet': ['hi', 'hello', 'hey'],
    'goodbye': ['bye', 'thanks', 'thank you', 'done']
}

def get_intent_and_entities(message):
    """
    Translates a message to English, then determines the user's intent and extracts entities.
    """
    # 1. Translate message to English first
    try:
        # Translate to English for consistent intent matching
        translated_message = GoogleTranslator(source='auto', target='en').translate(message)
        # Use .lower() for case-insensitive matching
        message_to_process = translated_message.lower()
    except Exception as e:
        print(f"Translation error: {e}")
        # If translation fails, work with the original message
        message_to_process = message.lower()

    # 2. Intent Recognition
    matched_intent = None
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in message_to_process for keyword in keywords):
            matched_intent = intent
            break

    # 3. Entity Extraction (for account number)
    account_number = None
    # Use the original message for entity extraction to get the exact account number
    match = re.search(r'acc\d+', message.lower())
    if match:
        account_number = match.group(0).upper()
        # If we find an account number, the intent is likely to get history
        matched_intent = 'get_customer_history'

    return matched_intent, account_number