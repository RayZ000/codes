import os
from faster_whisper import WhisperModel

# --- Configuration ---
# Folder where your audio files are located.
AUDIO_FOLDER = "/Volumes/HezeSamsung/Lectures/COMSOLIndianGuide/audOnly"
# Allowed audio file extensions.
AUDIO_EXTENSIONS = [".wav", ".mp3", ".flac", ".ogg"]
# Progress message interval in seconds.
PROGRESS_INTERVAL = 30
# Language for transcription.
LANGUAGE = "en"
# Model identifier from Hugging Face (e.g., "distil-large-v3").
MODEL_ID = "distil-large-v3"
# ----------------------




def is_audio_file(filename: str) -> bool:
    """Check if a file is an audio file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)

# Load the model once (this will process all files using the same instance)
model = WhisperModel(MODEL_ID)

# Process each audio file in the folder.
for filename in os.listdir(AUDIO_FOLDER):
    if is_audio_file(filename):
        audio_path = os.path.join(AUDIO_FOLDER, filename)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(AUDIO_FOLDER, base_name + ".txt")
        
        print(f"\nProcessing file: {audio_path}")
        
        # Transcribe the entire audio file (no chunk_length_s parameter)
        segments, info = model.transcribe(
            audio_path,
            language=LANGUAGE,
            condition_on_previous_text=False
        )
        
        transcript_lines = []
        next_progress = PROGRESS_INTERVAL
        
        # Iterate over all segments and collect text.
        for segment in segments:
            transcript_lines.append(segment.text)
            # Every time we pass a 30-second boundary, print a progress message.
            if segment.start >= next_progress:
                print(f"Reached approximately {int(segment.start)} seconds in '{filename}'")
                next_progress += PROGRESS_INTERVAL
        
        # Combine all the segment texts into one full transcript.
        full_transcript = "\n".join(transcript_lines)
        
        # Write the full transcript to a text file in the same folder as the audio.
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_transcript)
        
        print(f"Transcription saved to: {output_file}")