import soundfile as sf
from kokoro import KPipeline
import numpy as np

# Input file path
input_file = "/Users/raymond/Documents/rayZ/A-SBU/Ready for tts/2027 Xingyan Chen Thesis on Ultracold Molecules 1.md"  # Change to your file path, e.g., "input.md"

# Language and voice settings
lang_code = "a"          # American English (change as needed)
voice = "af_heart"       # Adjust to desired voice
speed = 1                # Speech speed
split_pattern = r"\n+"   # Split on newlines

# Initialize the text-to-speech pipeline
pipeline = KPipeline(lang_code=lang_code)

# Read the content from the input file
with open(input_file, "r", encoding="utf-8") as f:
    text_content = f.read()

# Generate audio using the pipeline
generator = pipeline(text_content, voice=voice, speed=speed, split_pattern=split_pattern)

# Collect all audio segments
all_audio = []

for i, (graphemes, phonemes, audio) in enumerate(generator):
    print(f"Segment {i}")
    print("Graphemes:", graphemes)
    print("Phonemes:", phonemes)
    all_audio.append(audio)

# Combine all audio segments into a single array
combined_audio = np.concatenate(all_audio)

# Save the combined audio to a single WAV file
output_file = "/Volumes/HezeSamsung/Podcast/2027XingyanChenThesisOnUltracoldMolecules.wav"
sf.write(output_file, combined_audio, 24000)
print(f"Saved combined audio to {output_file}")