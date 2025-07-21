import re
import nltk
from nltk.tokenize import sent_tokenize
from sensitive_utils.encryptor import encrypt_text, sensitive_data_log
from sensitive_utils.rag_faiss import LightweightRAG


PATTERNS = [
    (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', 'PAN'),
    (r'\b\d{4}\s?\d{4}\s?\d{4}\b', 'AADHAAR'),
    (r'\b[6-9]\d{9}\b', 'PHONE'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', 'EMAIL'),
    (r'\b\d{9,18}\b', 'ACCOUNT'),
    (r'\b\d{4,6}\b', 'PIN'), # Added PIN pattern
]

rag = LightweightRAG()

def detect_and_encrypt_sensitive(text: str) -> str:
    sensitive_data_log.clear()
    sentences = sent_tokenize(text)
    new_sentences = []

    for sent in sentences:
        found = False
        # Correctly nested loop for pattern matching
        for pattern, label in PATTERNS:
            matches = re.findall(pattern, sent)
            for match in matches:
                sent = sent.replace(match, encrypt_text(match, label))
                found = True

        if not found:
            example, label, distance = rag.query(sent)
            if distance < 0.5:
                sent = encrypt_text(sent, label)

        new_sentences.append(sent)

    return " ".join(new_sentences)