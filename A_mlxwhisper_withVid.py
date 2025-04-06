# %%
import os
import subprocess
import mlx_whisper

# --- Configuration ---
AUDIO_FOLDERS = [
    '/Volumes/HezeORICO/life/Huberman Lab', '/Volumes/HezeORICO/life/独树不成林'# , '/path/to/third/folder'
]

# Audio file extensions
AUDIO_EXTENSIONS = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]
# Video file extensions that should be processed
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv"]
PROGRESS_INTERVAL = 300
# Model repository identifier from Hugging Face.
MODEL_ID = "mlx-community/whisper-large-v3-turbo"
# ----------------------

def is_audio_file(filename: str) -> bool:
    """Check if a file is an audio file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)

def is_video_file(filename: str) -> bool:
    """Check if a file is a video file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)

# Process each folder in AUDIO_FOLDERS.
for folder in AUDIO_FOLDERS:
    print(f"\nProcessing folder: {folder}")
    for filename in os.listdir(folder):
        # Skip hidden files and system files.
        if filename.startswith('._'):
            continue
        
        # Compute base name and output file path
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(folder, base_name + ".txt")
        
        # If the transcript already exists, skip processing this file
        if os.path.exists(output_file):
            print(f"Output file {output_file} already exists. Skipping {filename}.")
            continue
        
        file_path = os.path.join(folder, filename)
        input_path = None  # will be set to the file to transcribe
        
        if is_audio_file(filename):
            input_path = file_path
        elif is_video_file(filename):
            # Extract audio from video using ffmpeg.
            temp_audio_path = os.path.join(folder, base_name + "_extracted.mp3")
            print(f"\nExtracting audio from video file: {file_path}")
            ffmpeg_command = ["ffmpeg", "-y", "-i", file_path, "-q:a", "0", "-map", "a", temp_audio_path]
            subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            input_path = temp_audio_path
        else:
            # Skip files that are neither audio nor video.
            continue
        
        print(f"\nProcessing file: {input_path}")
        
        # Transcribe the file using mlx_whisper.
        result = mlx_whisper.transcribe(
            input_path,
            path_or_hf_repo=MODEL_ID
        )
        
        # Use the full transcript from the "text" key.
        full_transcript = result["text"]
        
        # Optionally, log progress based on the segments.
        next_progress = PROGRESS_INTERVAL
        for segment in result["segments"]:
            if segment["start"] >= next_progress:
                print(f"Reached approximately {int(segment['start'])} seconds in '{filename}'")
                next_progress += PROGRESS_INTERVAL
        
        # Write the full transcript to a text file.
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_transcript)
        
        print(f"Transcription saved to: {output_file}")
        
        # If a temporary audio file was created from a video, remove it.
        if is_video_file(filename) and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path) 

# %%
