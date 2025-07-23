import re
from deep_translator import GoogleTranslator

# --- NEW: Add keywords for specific follow-up questions ---
INTENT_KEYWORDS = {
    'get_customer_list': ['list', 'customers', 'customer', 'accounts', 'users'],
    'get_customer_history': ['history', 'details', 'info', 'information', 'about'],
    'get_due_amount': ['due', 'outstanding', 'balance', 'owe'],
    'get_payment_record': ['record', 'payment history', 'payments'],
    'greet': ['hi', 'hello', 'hey'],
    'goodbye': ['bye', 'thanks', 'thank you', 'done']
}

def get_intent_and_entities(message):
    """
    Translates a message, then determines the user's intent and extracts entities.
    """
    try:
        translated_message = GoogleTranslator(source='auto', target='en').translate(message)
        message_to_process = translated_message.lower()
    except Exception as e:
        print(f"Translation error: {e}")
        message_to_process = message.lower()

    # --- Intent Recognition ---
    matched_intent = None
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in message_to_process for keyword in keywords):
            matched_intent = intent
            break
            
    # --- Entity Extraction (for account number) ---
    account_number = None
    match = re.search(r'acc\d+', message.lower())
    if match:
        account_number = match.group(0).upper()
        # If we find an account number, the intent is likely to get history
        matched_intent = 'get_customer_history'
        
    return matched_intent, account_number