import os
import torch
from transformers import pipeline

# Manually add local ffmpeg path
os.environ["PATH"] += os.pathsep + os.path.abspath("ffmpeg/bin")

# Load Whisper (small model = faster, lower memory)
asr_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-small", device=0 if torch.cuda.is_available() else -1)

def transcribe_audio(file_path: str) -> str:
    result = asr_pipeline(file_path, generate_kwargs={"language": "en", "task": "transcribe"})
    return result["text"]


