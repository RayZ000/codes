# GEM https://docs.nexa.ai/sdk/python-interface/gguf
import os
from nexa.gguf import NexaVoiceInference

# --- Configuration: Modify these variables as needed ---
# Folder where your audio files are located.
AUDIO_FOLDER = "/Volumes/HezeSamsung/codes/nexa try py"  
# Model identifier to use for transcription.
MODEL_PATH = "OllmOne/whisper-large-v3-GGUF"
LOCAL_PATH = "/Volumes/HezeSamsung/llm/whisperV3Large.gguf"
# Other model parameters; adjust if needed.
BEAM_SIZE = 5
LANGUAGE = None         # Use a language code like "en" if desired.
TASK = "transcribe"
TEMPERATURE = 0.0
COMPUTE_TYPE = "default"
# -----------------------------------------------------------

# Initialize the NexaVoiceInference instance.
inference = NexaVoiceInference(
    model_path=MODEL_PATH,
    local_path=None,
    beam_size=BEAM_SIZE,
    language=LANGUAGE,
    task=TASK,
    temperature=TEMPERATURE,
    compute_type=COMPUTE_TYPE
)

# Define which file extensions to consider as audio files.
AUDIO_EXTENSIONS = [".wav", ".mp3", ".flac", ".ogg"]

def is_audio_file(filename: str) -> bool:
    """Return True if the filename ends with one of the allowed audio extensions."""
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)

# Iterate over all files in the specified folder.
for filename in os.listdir(AUDIO_FOLDER):
    if is_audio_file(filename):
        audio_path = os.path.join(AUDIO_FOLDER, filename)
        print(f"Transcribing: {audio_path}")
        
        # Transcribe the audio file.
        transcript = inference.transcribe(audio_path)
        
        # Save the transcript to a text file with the same base name.
        output_file = os.path.join(AUDIO_FOLDER, os.path.splitext(filename)[0] + ".txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        print(f"Transcription saved to: {output_file}")