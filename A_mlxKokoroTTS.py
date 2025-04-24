# kokoro does the truncation for us, so we don't need to worry about it, just feed the text

import os
import subprocess
import glob
import soundfile as sf
import numpy as np
import time

# Start the timer
start_time = time.time()

# Define file paths and parameters
input_file = '/Volumes/HezeSamsung/Lectures/MAR/pod0424/text.md'
# Set the desired name for the final merged WAV file
final_wav_filename = "MARpod0424.wav"
# Change this to your desired output folder where the WAV files will be created
output_folder = '/Volumes/HezeSamsung/Podcast'
model_name = "mlx-community/Kokoro-82M-8bit"

# MARpod0310_midterm2
# 0303ML_in_S-SNOM
# JCnaiyuMar27

# Read the input text
with open(input_file, "r", encoding="utf-8") as f:
    text_content = f.read()

# Build the TTS command
command = [
    "python",
    "-m",
    "mlx_audio.tts.generate",
    "--model", model_name,
    "--text", text_content
]

# Run the TTS command in the output folder so that the WAV files are created there
subprocess.run(command, cwd=output_folder, check=True)
print("TTS generation complete.")

# Merge the generated WAV files in name order.
# It assumes the files are named like audio_001.wav, audio_002.wav, etc.
wav_files = sorted(glob.glob(os.path.join(output_folder, "audio_*.wav")))
print("Found WAV files:", wav_files)

merged_audio = []
samplerate = None

for wav_file in wav_files:
    audio, sr = sf.read(wav_file)
    if samplerate is None:
        samplerate = sr
    elif sr != samplerate:
        print(f"Warning: sample rate mismatch in {wav_file}.")
    merged_audio.append(audio)

if merged_audio:
    merged_audio = np.concatenate(merged_audio)
    merged_output_file = os.path.join(output_folder, final_wav_filename)
    sf.write(merged_output_file, merged_audio, samplerate)
    print("Merged audio saved as", merged_output_file)
else:
    print("No audio files found to merge.")

# Delete the raw WAV files
for wav_file in wav_files:
    os.remove(wav_file)
    print(f"Deleted {wav_file}")

# Calculate and output total running time
end_time = time.time()
runtime = end_time - start_time
print(f"Total running time: {runtime:.2f} seconds")