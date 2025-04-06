import nexa

def transcribe_audio(audio_path: str, output_path: str) -> None:
    """
    Transcribe an audio file using the whisper-large-v3-turbo model via the Nexa SDK Python API.
    
    Parameters:
        audio_path (str): Path to the input audio file.
        output_path (str): Path to save the transcription text.
    """
    # Load the transcription model (make sure the model identifier is correct).
    model = nexa.load_model("whisper-large-v3-turbo")
    
    # Perform transcription on the input audio.
    result = model.transcribe(audio_path)
    
    # If the result is a dictionary with a "text" key, extract the transcription.
    transcription = result.get("text", result) if isinstance(result, dict) else result

    # Write the transcription to the output file.
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(transcription)
    
    print(f"Transcription saved to {output_path}")

# Modify these variables with your desired paths.
AUDIO_FILE = "path/to/your/audio.wav"          # Input audio file path.
OUTPUT_FILE = "path/to/output/transcription.txt"  # Output transcription file path.

if __name__ == "__main__":
    transcribe_audio(AUDIO_FILE, OUTPUT_FILE)