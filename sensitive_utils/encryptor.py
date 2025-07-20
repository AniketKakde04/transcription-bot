import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
fernet = Fernet(os.getenv("FERNET_KEY").encode())
sensitive_data_log = {}

def encrypt_text(text: str, label: str = "SENSITIVE") -> str:
    encrypted = fernet.encrypt(text.encode()).decode()
    token_label = f"***{label.upper()}***"
    sensitive_data_log[token_label] = encrypted
    return token_label

def decrypt_text(token_label: str) -> str:
    token = sensitive_data_log.get(token_label)
    if token:
        return fernet.decrypt(token.encode()).decode()
    return token_label
