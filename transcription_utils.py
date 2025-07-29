import os
import torch
from transformers import pipeline

# Manually add local ffmpeg path if you need it for local testing
os.environ["PATH"] += os.pathsep + os.path.abspath("ffmpeg/bin")

# Load Whisper (small model = faster, lower memory)
asr_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-small", device=0 if torch.cuda.is_available() else -1)

def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribes audio data directly from memory (bytes).
    """
    # The pipeline can directly accept raw audio bytes
    result = asr_pipeline(audio_data, generate_kwargs={"language": "en", "task": "transcribe"})
    return result["text"]